"""
build_state.py — 从 .agent-logs/project-events.jsonl 重建项目根目录 STATE.json

数据源：
   1) 事件日志：.agent-logs/project-events.jsonl（已由 report_event_server 过滤
     并维护 phase 链连续性；默认；可由 --log 覆盖）
  2) phases/ 目录结构（用于枚举所有 phase 与 task 节点；不读任何 .md 正文）

约束：
  - 不再需要"选最新 phase-01 序列"的逻辑：phase 链的连续性由 MCP 维护
  - 状态完全由 log 事件推导；不读 task 文件的 YAML
  - STATE.json 不再含 description / dependencies / plan_path 字段（template 去除）
  - phases/phase-XX-<name>/ 目录存在 → 该 phase 必出
  - phase 下 tasks/ 下每份 TASK-NNN-*.md → 该 task 必出（无事件 → 全 pending）
  - task_folder 直接由 phase 目录名构造
  - 每次被调用都重新生成 STATE.json（无论时间戳新旧）

入口：refresh_state.py 统一调用 main_pipeline，不再提供独立 CLI。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from _common import (
    PHASE_DIR_RE,
    TASK_FILE_RE,
    PROJECT_ROOT,
    extract_phase,
    extract_task_id,
    list_phases,
    list_tasks,
    normalize_path,
)
DEFAULT_LOG_PATH = PROJECT_ROOT / ".agent-logs" / "project-events.jsonl"
DEFAULT_TEMPLATE_PATH = PROJECT_ROOT / ".templates" / "STATE.json"
DEFAULT_STATE_PATH = PROJECT_ROOT / "STATE.json"

INITIAL_TASK_STATUS = {
    "implementation": "pending",
    "review": "pending",
    "test": "pending",
}


# ───────────────────────── IO ─────────────────────────

def read_template(template_path: Path = DEFAULT_TEMPLATE_PATH) -> dict[str, Any]:
    if not template_path.exists():
        sys.exit(f"[build_state] 模板不存在: {template_path}")
    with template_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_events(log_path: Path = DEFAULT_LOG_PATH) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    events: list[dict[str, Any]] = []
    with log_path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(
                    f"[build_state] 跳过第 {lineno} 行（JSON 解析失败）: {e}",
                    file=sys.stderr,
                )
    return events


def write_state(state: dict[str, Any], state_path: Path = DEFAULT_STATE_PATH) -> None:
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ───────────────── 事件分组 ─────────────────

def group_events_by_task(
    events: list[dict[str, Any]],
) -> dict[tuple[int, str], list[dict[str, Any]]]:
    """按 (phase_num, task_id) 分组 task 级别事件。
    PHASE_PLAN_COMPLETED 是 phase 级，不归入 task 列表。
    task_path 不规范或缺 → 跳过该事件。"""
    out: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for ev in events:
        if ev.get("event_type") == "PHASE_PLAN_COMPLETED":
            continue
        payload = ev.get("payload") or {}
        tp = payload.get("task_path")
        if not tp:
            continue
        num, _ = extract_phase(tp)
        if num is None:
            continue
        tid = extract_task_id(tp)
        if not tid:
            continue
        out.setdefault((num, tid), []).append(ev)
    return out


def find_phase_plan_event(
    events: list[dict[str, Any]], phase_num: int
) -> dict[str, Any] | None:
    """返回该 phase 的 PHASE_PLAN_COMPLETED 事件（应唯一）。"""
    for ev in events:
        if ev.get("event_type") != "PHASE_PLAN_COMPLETED":
            continue
        payload = ev.get("payload") or {}
        pp = payload.get("task_folder")
        if not pp:
            continue
        n, _ = extract_phase(pp)
        if n == phase_num:
            return ev
    return None


# ───────────────── Explorer 事件 ─────────────────

def group_explorer_events_by_phase(
    events: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    """按 phase_num 分组 Explorer 事件。payload.phase 字段判定归属。"""
    out: dict[int, list[dict[str, Any]]] = {}
    for ev in events:
        et = ev.get("event_type", "")
        if not et.startswith("EXPLORER_"):
            continue
        payload = ev.get("payload") or {}
        phase_str = payload.get("phase", "")
        n, _ = extract_phase(phase_str)
        if n is None:
            # 兼容 "phase-01" 无后缀格式（explorer 事件 payload）
            m = re.match(r"phase-(\d{2})$", phase_str)
            if m:
                n = int(m.group(1))
            else:
                continue
        out.setdefault(n, []).append(ev)
    return out


def derive_exploration_status(
    events: list[dict[str, Any]],
    all_tasks_complete: bool,
) -> dict[str, Any]:
    """根据 Explorer 事件 + task 完成状态推导 exploration 字段。

    - all_tasks_complete=False → pending（尚未到探索阶段）
    - all_tasks_complete=True + 无 EXPLORER_COMPLETED/SKIPPED → pending（ready，待探索）
    - all_tasks_complete=True + 有 EXPLORER_COMPLETED → completed，rounds 不变
    - all_tasks_complete=True + 有 EXPLORER_SKIPPED → skipped
    - EXPLORER_FOUND → rounds+1，status 保持 pending（表示有发现待修复，orchestrator 后续重新调度）
    """
    if not all_tasks_complete:
        return {"status": "pending", "rounds": 0, "last_run_at": None, "last_discovery_count": 0}

    rounds = 0
    last_run_at = None
    last_discovery_count = 0
    status = "pending"

    for ev in sorted(events, key=lambda e: e.get("timestamp", "")):
        et = ev.get("event_type", "")
        ts = ev.get("timestamp", "")
        payload = ev.get("payload") or {}

        if et == "EXPLORER_COMPLETED":
            status = "completed"
            last_run_at = ts
            last_discovery_count = payload.get("discovery_count", 0)
        elif et == "EXPLORER_SKIPPED":
            status = "skipped"
            last_run_at = ts
        elif et == "EXPLORER_FOUND":
            rounds += 1
            last_run_at = ts
            last_discovery_count = payload.get("discovery_count", 0)
            # status 保持 pending
        # EXPLORER_INPROGRESS 不推导状态

    return {
        "status": status,
        "rounds": rounds,
        "last_run_at": last_run_at,
        "last_discovery_count": last_discovery_count,
    }


# ───────────────── 状态推导 ─────────────────

def derive_task_status(events: list[dict[str, Any]]) -> dict[str, Any]:
    """根据该 task 的事件流推导 task 完整状态对象。"""
    status = dict(INITIAL_TASK_STATUS)
    review_rejections = 0
    test_failures = 0
    last_event_type: str | None = None
    last_agent: str | None = None
    last_ts: str | None = None
    first_ts: str | None = None

    for ev in sorted(events, key=lambda e: e.get("timestamp", "")):
        ts = ev.get("timestamp", "")
        if first_ts is None:
            first_ts = ts
        last_ts = ts
        last_event_type = ev.get("event_type")
        last_agent = ev.get("agent_name")
        et = ev.get("event_type")

        # 仅终态事件推导状态；INPROGRESS 仅记审计，不推导（防卡死 running）
        if et == "TDD_COMPLETED":
            status["implementation"] = "completed"
            status["review"] = "pending"
            status["test"] = "pending"
        elif et == "TDD_FAILED":
            status["implementation"] = "failed"
            status["review"] = "pending"
            status["test"] = "pending"
        elif et == "REVIEW_COMPLETED":
            status["review"] = "completed"
            status["test"] = "pending"
        elif et == "REVIEW_FAILED":
            status["review"] = "failed"
            review_rejections += 1
            status["test"] = "pending"
        elif et == "TEST_COMPLETED":
            status["test"] = "completed"
        elif et == "TEST_FAILED":
            status["test"] = "failed"
            test_failures += 1

    return {
        "status": status,
        "review_rejections": review_rejections,
        "test_failures": test_failures,
        "last_event_type": last_event_type,
        "last_agent": last_agent,
        "created_at": first_ts,
        "updated_at": last_ts,
    }


def _task_is_complete(task: dict[str, Any]) -> bool:
    """task 所有阶段均为 completed。"""
    for phase, value in task["status"].items():
        if value != "completed":
            return False
    return True


def derive_phase_status(tasks: dict[str, dict[str, Any]]) -> str:
    """phase 状态：全部 task 完成 → completed，否则 running。"""
    if not tasks:
        return "running"
    for t in tasks.values():
        if not _task_is_complete(t):
            return "running"
    return "completed"


# ───────────────── 构造 STATE ─────────────────

def build_state(
    template: dict[str, Any],
    events: list[dict[str, Any]],
    project_root: Path,
) -> dict[str, Any]:
    """从日志事件 + phases 目录结构构造 STATE。"""
    phases_on_disk = list_phases(project_root / "phases")
    if not phases_on_disk:
        return {}

    events_by_task = group_events_by_task(events)
    explorer_events_by_phase = group_explorer_events_by_phase(events)

    phases_out: dict[str, Any] = {}
    completed_count = 0
    running_count = 0
    max_phase_num = phases_on_disk[-1][0]

    for phase_num, suffix, phase_dir in phases_on_disk:
        phase_id = f"phase-{phase_num:02d}"
        phase_dir_name = phase_dir.name
        task_folder = f"phases/{phase_dir_name}/tasks/"

        plan_ev = find_phase_plan_event(events, phase_num)
        created_at = plan_ev.get("timestamp") if plan_ev else None
        updated_at = created_at

        # 该 phase 下所有 task
        tasks_out: dict[str, Any] = {}
        for task_id, task_path in list_tasks(phase_dir / "tasks"):
            task_rel = normalize_path(str(task_path), project_root)
            tev = events_by_task.get((phase_num, task_id), [])
            derived = derive_task_status(tev)
            tasks_out[task_id] = {
                "task_id": task_id,
                "task_path": task_rel,
                "status": derived["status"],
                "review_rejections": derived["review_rejections"],
                "test_failures": derived["test_failures"],
                "last_event_type": derived["last_event_type"],
                "last_agent": derived["last_agent"],
                "created_at": derived["created_at"],
                "updated_at": derived["updated_at"],
            }
            if derived["updated_at"] and derived["updated_at"] > (updated_at or ""):
                updated_at = derived["updated_at"]

        all_tasks_complete = derive_phase_status(tasks_out) == "completed"
        explorer_evs = explorer_events_by_phase.get(phase_num, [])
        exploration = derive_exploration_status(explorer_evs, all_tasks_complete)

        tasks_done = all_tasks_complete
        exploration_done = exploration["status"] in ("completed", "skipped")
        phase_status = "completed" if (tasks_done and exploration_done) else "running"

        if phase_status == "completed":
            completed_count += 1
        else:
            running_count += 1

        phases_out[phase_id] = {
            "phase_id": phase_id,
            "name": suffix,
            "status": phase_status,
            "task_folder": task_folder,
            "created_at": created_at,
            "updated_at": updated_at,
            "exploration": exploration,
            "tasks": tasks_out,
        }

    # current_phase：选 running 中 phase_num 最小的；否则取 max_phase_num
    current_phase = f"phase-{max_phase_num:02d}"
    for num, _, _ in phases_on_disk:
        pid = f"phase-{num:02d}"
        if phases_out[pid]["status"] == "running":
            current_phase = pid
            break

    all_ts = [ev.get("timestamp", "") for ev in events if ev.get("timestamp")]
    last_updated = max(all_ts) if all_ts else None

    return {
        "schema_version": template.get("schema_version", "1.0"),
        "last_updated": last_updated,
        "current_phase": current_phase,
        "total_phases": max_phase_num,
        "completed_phases": completed_count,
        "active_phases": running_count,
        "phases": phases_out,
    }


# ───────────────── 主流程 ─────────────────

def main_pipeline(
    project_root: Path = PROJECT_ROOT,
    log_path: Path = DEFAULT_LOG_PATH,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
    state_path: Path = DEFAULT_STATE_PATH,
) -> str:
    """返回执行结果标签：
      - "no_events"   日志为空
      - "empty_state" phases 目录为空
      - "ok"          成功写入
    """
    template = read_template(template_path)
    events = read_events(log_path)
    if not events:
        print("[build_state] 日志为空，跳过生成")
        return "no_events"

    state = build_state(template, events, project_root)
    if not state:
        print("[build_state] phases 目录为空，跳过生成")
        return "empty_state"

    write_state(state, state_path)
    print(f"[build_state] 已写入 {state_path}")
    return "ok"
