#!/usr/bin/env python3
"""schedule.py — orchestrator 调度决策脚本

替代 orchestrator.md Step 2~Step 6 的全部决策逻辑。
读取 STATE.json / task_graph.json / 目录结构，输出 JSON 格式的调度决策。

用法：
    python .bin/schedule.py

输出：stdout 一行 JSON，stderr 诊断信息。
退出码：0 正常（含 blocked/done），1 致命错误。

输出字段说明：
    decision    str   调度决策。枚举值：schedule / condense / blocked / done
    targets     list  当 decision=schedule 时有效，数组元素每项含
                       {subagent_type: str, params: str}
                       subagent_type 透传给 task 工具；params 是命令行风格参数字符串
    followup    str   subagent 返回后需执行的 bash 命令（如 save hash / get discoveries count）
    message     str   供 orchestrator 展示给用户的消息（blocked/done/condense 时有意义）

典型输出实例：

     # 调度 planner（首次启动）
     {"decision":"schedule","targets":[{"subagent_type":"planner","params":"--mode create"}],
      "followup":"python .bin/check_content_changed.py --save","message":null}

     # 调度 planner（specs 变更）
     {"decision":"schedule","targets":[{"subagent_type":"planner","params":"--mode update --source specs"}],
      "followup":"python .bin/check_content_changed.py --save","message":null}

     # 调度 planner（discoveries 变更）
     {"decision":"schedule","targets":[{"subagent_type":"planner","params":"--mode update --source discoveries"}],
      "followup":"python .bin/check_content_changed.py --save","message":null}

     # 调度 developer（单个 task）
    {"decision":"schedule","targets":[{"subagent_type":"developer",
     "params":"--task_path phases/phase-01-基础/tasks/TASK-001-环境搭建.md --entrance_type 新开发任务"}],
     "followup":null,"message":null}

    # 并行调度 developer（同 phase 无依赖的两个 task）
    {"decision":"schedule","targets":[
     {"subagent_type":"developer","params":"--task_path phases/phase-03-并行/tasks/TASK-001-功能A.md --entrance_type 新开发任务"},
     {"subagent_type":"developer","params":"--task_path phases/phase-03-并行/tasks/TASK-002-功能B.md --entrance_type 新开发任务"}],
     "followup":null,"message":null}

    # 调度 reviewer
    {"decision":"schedule","targets":[{"subagent_type":"reviewer",
     "params":"--task_path phases/phase-01-基础/tasks/TASK-001-环境搭建.md"}],
     "followup":null,"message":null}

    # 调度 tester
    {"decision":"schedule","targets":[{"subagent_type":"tester",
     "params":"--task_path phases/phase-01-基础/tasks/TASK-001-环境搭建.md"}],
     "followup":null,"message":null}

    # 调度 explorer（探索完成后需执行 followup 命令判定是否修复或结束）
    {"decision":"schedule","targets":[{"subagent_type":"explorer","params":"--phase phase-01"}],
     "followup":"python .bin/get_discoveries_count.py --phase phase-01","message":null}

    # 复盘 phase（knowledge-condenser skill）
    {"decision":"condense","targets":null,"followup":null,
     "message":"phase phase-01 任务全部完成，调用 knowledge-condenser skill 复盘"}

    # 阻塞（用户需介入）
    {"decision":"blocked","targets":null,"followup":null,
     "message":"task TASK-001 已达重试上限（review_rejections=5），等待用户决策"}

    # 全部完成
    {"decision":"done","targets":null,"followup":null,
     "message":"全部 phase 完成，调度结束"}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from _common import PROJECT_ROOT

STATE_PATH = PROJECT_ROOT / "STATE.json"
GRAPH_PATH = PROJECT_ROOT / "task_graph.json"
PHASES_DIR = PROJECT_ROOT / "phases"

RETRY_LIMIT = 5
EXPLORER_ROUND_LIMIT = 20


def emit(decision: str, targets: list[dict] | None = None, followup: str | None = None, message: str | None = None) -> None:
    """输出调度决策 JSON 到 stdout。"""
    out: dict[str, Any] = {"decision": decision}
    out["targets"] = targets if targets else None
    out["followup"] = followup
    out["message"] = message
    print(json.dumps(out, ensure_ascii=False))


def run_script(script: str, *args: str) -> tuple[int, str, str]:
    """运行 .bin/ 下的脚本，返回 (returncode, stdout, stderr)。"""
    cmd = [sys.executable, str(PROJECT_ROOT / ".bin" / script), *args]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(PROJECT_ROOT))
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def task_fully_completed(task: dict) -> bool:
    """task 的 implementation/review/test 均为 completed。"""
    s = task["status"]
    return s["implementation"] == "completed" and s["review"] == "completed" and s["test"] == "completed"


def all_tasks_completed(phase: dict) -> bool:
    """phase 内所有 task 全部 completed。"""
    tasks = phase.get("tasks", {})
    if not tasks:
        return False
    return all(task_fully_completed(t) for t in tasks.values())


def deps_satisfied(task_id: str, graph: dict, state: dict) -> bool:
    """检查 task 的所有依赖是否全部 completed。"""
    node_id = None
    for node in graph.get("nodes", []):
        if node["phase"] == state.get("_current_phase_id") and node["task_id"] == task_id:
            node_id = node["id"]
            break
    if node_id is None:
        return True
    node_obj = next((n for n in graph["nodes"] if n["id"] == node_id), None)
    if node_obj is None:
        return True
    for dep_id in node_obj.get("dependencies", []):
        dep_phase, dep_task = dep_id.split("/")
        phase = state["phases"].get(dep_phase)
        if phase is None:
            return False
        dep_task_obj = phase.get("tasks", {}).get(dep_task)
        if dep_task_obj is None or not task_fully_completed(dep_task_obj):
            return False
    return True


def determine_task_action(task: dict) -> tuple[str, str] | None:
    """根据 task status 返回 (subagent_type, params_suffix) 或 None（跳过）。

    返回的 params_suffix 不含 --task_path，调用方拼上。
    """
    s = task["status"]
    if s["implementation"] == "pending":
        return ("developer", "--entrance_type 新开发任务")
    if s["implementation"] == "failed":
        return ("developer", "--entrance_type 重试")
    if s["implementation"] == "completed":
        if s["review"] == "pending":
            return ("reviewer", "")
        if s["review"] == "failed":
            return ("developer", "--entrance_type review打回")
        if s["review"] == "completed":
            if s["test"] == "pending":
                return ("tester", "")
            if s["test"] == "failed":
                return ("developer", "--entrance_type test打回")
    return None


def find_schedulable_tasks(phase_id: str, phase: dict, graph: dict, state: dict) -> list[dict]:
    """在同一 phase 内找出所有可调度的 task（依赖已满足 + 有待执行动作）。

    返回 [{"subagent_type": ..., "params": ...}, ...]
    """
    targets: list[dict] = []
    state["_current_phase_id"] = phase_id
    for task_id in sorted(phase.get("tasks", {}).keys()):
        task = phase["tasks"][task_id]

        if task["review_rejections"] >= RETRY_LIMIT:
            continue
        if task["test_failures"] >= RETRY_LIMIT:
            continue

        if not deps_satisfied(task_id, graph, state):
            continue

        action = determine_task_action(task)
        if action is None:
            continue

        subagent_type, suffix = action
        task_path = task["task_path"]
        params = f"--task_path {task_path}"
        if suffix:
            params += f" {suffix}"
        targets.append({"subagent_type": subagent_type, "params": params})

    state.pop("_current_phase_id", None)
    return targets


def has_condensed(phase_dir_name: str) -> bool:
    """检查 phase 目录下是否有 .condensed 标记文件。"""
    marker = PHASES_DIR / phase_dir_name / ".condensed"
    return marker.exists()


def main() -> int:
    # ── Step 2: 变更检测 ──
    rc, stdout, stderr = run_script("refresh_state.py")
    if rc != 0:
        emit("blocked", message=f"refresh_state.py 失败: {stderr}")
        return 0

    rc, stdout, stderr = run_script("check_content_changed.py", "--check")
    if rc != 0:
        emit("blocked", message=f"specs/ 不存在或不可读: {stderr}")
        return 0

    changed = []
    try:
        changed = json.loads(stdout) if stdout else []
    except json.JSONDecodeError:
        changed = []

    if changed:
        # ── Step 3: 调度 Planner ──
        rc2, stdout2, _ = run_script("check_phases_existed.py")
        mode = "update" if stdout2.strip() == "true" else "create"
        params = f"--mode {mode}"
        if mode == "update":
            source = changed[0] if len(changed) == 1 else "all"
            params += f" --source {source}"
        emit(
            "schedule",
            targets=[{"subagent_type": "planner", "params": params}],
            followup=f"python .bin/check_content_changed.py --save",
        )
        return 0

    # ── Step 4: 读取状态 ──
    if not STATE_PATH.exists():
        emit("blocked", message="STATE.json 不存在，请先运行 planner 生成 phases")
        return 0

    with STATE_PATH.open("r", encoding="utf-8") as f:
        state: dict[str, Any] = json.load(f)

    if not GRAPH_PATH.exists():
        emit("blocked", message="task_graph.json 不存在")
        return 0

    with GRAPH_PATH.open("r", encoding="utf-8") as f:
        graph: dict[str, Any] = json.load(f)

    phases = state.get("phases", {})
    if not phases:
        emit("done", message="无 phase，调度结束")
        return 0

    # ── 检查全部完成 ──
    all_completed = all(p["status"] == "completed" for p in phases.values())
    if all_completed:
        all_condensed = all(has_condensed(p["task_folder"].split("/")[1]) for p in phases.values())
        if all_condensed:
            emit("done", message="全部 phase 完成，调度结束")
            return 0

    # ── Step 5 + Step 6: 遍历 phases ──
    for phase_id in sorted(phases.keys()):
        phase = phases[phase_id]
        phase_dir_name = phase["task_folder"].split("/")[1]

        # 跳过已完成且已 condensed 的 phase
        if phase["status"] == "completed" and has_condensed(phase_dir_name):
            continue

        tasks_complete = all_tasks_completed(phase)
        if not tasks_complete:
            # ── Step 6: Phase 内调度 ──
            # 检查重试上限
            for task_id in sorted(phase.get("tasks", {}).keys()):
                task = phase["tasks"][task_id]
                if task["review_rejections"] >= RETRY_LIMIT:
                    emit("blocked", message=f"task {task_id} 已达重试上限（review_rejections={task['review_rejections']}），等待用户决策")
                    return 0
                if task["test_failures"] >= RETRY_LIMIT:
                    emit("blocked", message=f"task {task_id} 已达重试上限（test_failures={task['test_failures']}），等待用户决策")
                    return 0

            # 计算可并行调度的 targets
            targets = find_schedulable_tasks(phase_id, phase, graph, state)
            if targets:
                emit("schedule", targets=targets)
                return 0
            else:
                emit("blocked", message=f"phase {phase_id} 无可调度的 task（可能依赖未满足），等待上游完成")
                return 0

        # tasks 全部完成 → 检查 exploration
        exploration = phase.get("exploration", {})
        exp_status = exploration.get("status", "pending")

        if exp_status == "pending":
            # ── 调度 Explorer ──
            emit(
                "schedule",
                targets=[{"subagent_type": "explorer", "params": f"--phase {phase_id}"}],
                followup=f"python .bin/get_discoveries_count.py --phase {phase_id}",
            )
            return 0

        if exp_status in ("completed", "skipped"):
            # Explorer 返回后有 discoveries？
            # exploration.rounds 反映了 EXPLORER_FOUND 次数
            rounds = exploration.get("rounds", 0)
            if rounds >= EXPLORER_ROUND_LIMIT:
                emit("blocked", message=f"phase {phase_id} explorer 已达轮次上限（rounds={rounds}），等待用户介入")
                return 0

            # 检查 .condensed 标记
            if not has_condensed(phase_dir_name):
                emit("condense", message=f"phase {phase_id} 任务全部完成，调用 knowledge-condenser skill 复盘")
                return 0

            # 已 condensed，跳到下一 phase
            continue

    # 所有 phase 都已处理
    emit("done", message="全部 phase 完成，调度结束")
    return 0


if __name__ == "__main__":
    sys.exit(main())