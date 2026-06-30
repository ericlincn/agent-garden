"""
build_state.py — 从 .agent-logs/latest-project-events.jsonl 重建项目根目录 STATE.json

数据源：
  1) 事件日志：.agent-logs/latest-project-events.jsonl（已由 report-event-server 过滤
     并维护 phase 链连续性；默认；可由 --log 覆盖）
  2) phases/ 目录结构（用于枚举所有 phase 与 task 节点；不读任何 .md 正文）

约束：
  - 不再需要"选最新 phase-01 序列"的逻辑：phase 链的连续性由 MCP 维护
  - 状态完全由 log 事件推导；不读 task 文件的 YAML
   - STATE.json 不再含 description / dependencies / plan_path 字段（template 去除）
  - phases/phase-XX-<name>/ 目录存在 → 该 phase 必出
  - phase 下 tasks/ 下每份 TASK-NNN-*.md → 该 task 必出（无事件 → 全 pending）
   - task_folder 直接由 phase 目录名构造
  - 若 STATE.json 已存在，仅当 log 内最大 timestamp > existing.last_updated 才重写

用法：
  python build_state.py                       # 默认：根=脚本目录
  python build_state.py --root <dir>          # 覆盖项目根
  python build_state.py --log <jsonl>         # 覆盖 log 路径
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _common import (
    PHASE_DIR_RE,
    TASK_FILE_RE,
    extract_phase,
    extract_task_id,
    list_phases,
    list_tasks,
    normalize_path,
)

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = DEFAULT_PROJECT_ROOT / ".agent-logs" / "latest-project-events.jsonl"
DEFAULT_TEMPLATE_PATH = DEFAULT_PROJECT_ROOT / ".templates" / "STATE.json"
DEFAULT_STATE_PATH = DEFAULT_PROJECT_ROOT / "STATE.json"

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


def read_existing_state(state_path: Path = DEFAULT_STATE_PATH) -> dict[str, Any] | None:
    if not state_path.exists():
        return None
    try:
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


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

        # TDD 事件
        if et == "TDD_INPROGRESS":
            status["implementation"] = "running"
        elif et == "TDD_COMPLETED":
            status["implementation"] = "completed"
            status["review"] = "pending"
            status["test"] = "pending"
        elif et == "TDD_FAILED":
            status["implementation"] = "failed"
            status["review"] = "pending"
            status["test"] = "pending"
        elif et == "REVIEW_INPROGRESS":
            status["review"] = "running"
        elif et == "REVIEW_COMPLETED":
            status["review"] = "completed"
            status["test"] = "pending"
        elif et == "REVIEW_FAILED":
            status["review"] = "failed"
            review_rejections += 1
            status["test"] = "pending"
        elif et == "TEST_INPROGRESS":
            status["test"] = "running"
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

        phase_status = derive_phase_status(tasks_out)
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
    project_root: Path = DEFAULT_PROJECT_ROOT,
    log_path: Path = DEFAULT_LOG_PATH,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
    state_path: Path = DEFAULT_STATE_PATH,
) -> str:
    """返回执行结果标签：
      - "no_events"   日志为空
      - "stale"       log 时间戳不晚于已有 STATE.json
      - "empty_state" phases 目录为空
      - "ok"          成功写入
    """
    template = read_template(template_path)
    events = read_events(log_path)
    if not events:
        print("[build_state] 日志为空，跳过生成")
        return "no_events"

    all_ts = [ev.get("timestamp", "") for ev in events if ev.get("timestamp")]
    max_ts = max(all_ts) if all_ts else ""
    existing = read_existing_state(state_path)
    if existing and existing.get("last_updated") and max_ts <= existing["last_updated"]:
        print(
            f"[build_state] log 最大时间戳 {max_ts} 不晚于已有 STATE.json 的 "
            f"last_updated {existing['last_updated']}，跳过生成"
        )
        return "stale"

    state = build_state(template, events, project_root)
    if not state:
        print("[build_state] phases 目录为空，跳过生成")
        return "empty_state"

    write_state(state, state_path)
    print(f"[build_state] 已写入 {state_path}")
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从 latest-project-events.jsonl + phases 目录重建 STATE.json"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_PROJECT_ROOT,
        help="项目根目录（影响 phases/ 扫描与 STATE.json 输出）",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="事件日志路径（JSONL；默认 latest-project-events.jsonl）",
    )
    args = parser.parse_args()
    template_path = args.root / ".templates" / "STATE.json"
    state_path = args.root / "STATE.json"
    result = main_pipeline(
        project_root=args.root,
        log_path=args.log,
        template_path=template_path,
        state_path=state_path,
    )
    return 0 if result in ("ok", "no_events", "stale", "empty_state") else 1


if __name__ == "__main__":
    sys.exit(main())
