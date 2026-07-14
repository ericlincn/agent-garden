#!/usr/bin/env python3
"""check_task_dependencies.py — 检查 phases/ 下全部 task 文件的依赖正确性

检查项：
    1. 格式：dependencies 中每条必须为 phase-NN/TASK-NNN 格式，禁止裸 TASK-NNN
    2. 存在性：被依赖的 phase 和 task 必须实际存在
    3. 循环依赖：依赖图中不得存在环
    4. 自依赖：task 不得依赖自身

用法：
    python .bin/check_task_dependencies.py

输出：
    stdout — 检查摘要（OK / 发现 N 个问题）
    stderr — 逐条问题详情
退出码：0 无问题，1 有问题或错误。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import PROJECT_ROOT, list_phases, list_tasks, parse_frontmatter

PHASES_DIR = PROJECT_ROOT / "phases"

VALID_DEP_RE = re.compile(r"^phase-(\d{2})/TASK-(\d{3})$")
BARE_TASK_RE = re.compile(r"^TASK-(\d{3})$")


def parse_dependencies(value: str) -> list[str]:
    """从 frontmatter dependencies 字段值解析出依赖列表。"""
    if not value:
        return []
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
    if "|" in v:
        return [x for x in v.split("|") if x]
    return [v]


def collect_tasks() -> dict[str, dict]:
    """遍历 phases/，返回 {node_id: {"phase": ..., "task_id": ..., "path": ..., "deps": [...]}}。"""
    nodes: dict[str, dict] = {}
    phases = list_phases(PHASES_DIR)
    for phase_num, _name, phase_dir in phases:
        phase_id = f"phase-{phase_num:02d}"
        for task_id, task_path in list_tasks(phase_dir / "tasks"):
            node_id = f"{phase_id}/{task_id}"
            try:
                fm = parse_frontmatter(task_path.read_text(encoding="utf-8"))
            except OSError:
                fm = {}
            deps = parse_dependencies(fm.get("dependencies", ""))
            nodes[node_id] = {
                "phase": phase_id,
                "task_id": task_id,
                "path": str(task_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "deps": deps,
            }
    return nodes


def check_format_and_existence(nodes: dict[str, dict]) -> list[str]:
    """检查格式合规 + 引用存在性，返回问题列表。"""
    problems: list[str] = []
    all_node_ids = set(nodes.keys())
    all_phase_ids = {n["phase"] for n in nodes.values()}

    for node_id, info in sorted(nodes.items()):
        for dep in info["deps"]:
            # 检查裸 TASK-NNN
            if BARE_TASK_RE.match(dep):
                problems.append(
                    f"[格式] {node_id} 依赖 '{dep}' 为裸 TASK-NNN 格式，"
                    f"必须写作 phase-NN/TASK-NNN"
                )
                continue

            # 检查是否符合 phase-NN/TASK-NNN
            m = VALID_DEP_RE.match(dep)
            if not m:
                problems.append(
                    f"[格式] {node_id} 依赖 '{dep}' 不符合 phase-NN/TASK-NNN 格式"
                )
                continue

            # 检查自依赖
            target = f"phase-{m.group(1)}/TASK-{m.group(2)}"
            if target == node_id:
                problems.append(
                    f"[自依赖] {node_id} 依赖自身"
                )
                continue

            # 检查 phase 存在
            target_phase = f"phase-{m.group(1)}"
            if target_phase not in all_phase_ids:
                problems.append(
                    f"[不存在] {node_id} 依赖 '{dep}'，phase {target_phase} 不存在"
                )
                continue

            # 检查 task 存在
            if target not in all_node_ids:
                problems.append(
                    f"[不存在] {node_id} 依赖 '{dep}'，task 不存在"
                )
                continue

    return problems


def check_cycles(nodes: dict[str, dict]) -> list[str]:
    """DFS 检测循环依赖，返回问题列表。"""
    # 构建邻接表（仅含已验证存在的依赖）
    all_node_ids = set(nodes.keys())
    adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for node_id, info in nodes.items():
        for dep in info["deps"]:
            m = VALID_DEP_RE.match(dep)
            if m:
                target = f"phase-{m.group(1)}/TASK-{m.group(2)}"
                if target in all_node_ids and target != node_id:
                    adj[node_id].append(target)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {nid: WHITE for nid in nodes}
    problems: list[str] = []

    def dfs(u: str, path: list[str]) -> None:
        color[u] = GRAY
        path.append(u)
        for v in adj.get(u, []):
            if color[v] == GRAY:
                cycle_start = path.index(v)
                cycle = path[cycle_start:] + [v]
                problems.append(f"[循环] {' → '.join(cycle)}")
            elif color[v] == WHITE:
                dfs(v, path)
        path.pop()
        color[u] = BLACK

    for nid in sorted(nodes.keys()):
        if color[nid] == WHITE:
            dfs(nid, [])

    return problems


def main() -> int:
    if not PHASES_DIR.is_dir():
        print("phases/ 目录不存在，无需检查", file=sys.stderr)
        return 0

    nodes = collect_tasks()
    if not nodes:
        print("phases/ 下无 task 文件，无需检查", file=sys.stderr)
        return 0

    problems: list[str] = []
    problems.extend(check_format_and_existence(nodes))
    problems.extend(check_cycles(nodes))

    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        print(f"发现 {len(problems)} 个问题", file=sys.stderr)
        return 1

    print(f"OK — {len(nodes)} 个 task，依赖全部正确", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
