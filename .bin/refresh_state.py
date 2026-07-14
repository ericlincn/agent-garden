"""
refresh_state.py — 一次性刷新 STATE.json + task_graph.json

合并原 build_state.py + build_task_graph.py 为单一入口，
将 orchestrator 每轮的 bash 调用从 3 次降为 1 次，
减少 agent 上下文消耗和"中途停住"的概率。

用法：
  python .bin/refresh_state.py
  python .bin/refresh_state.py --root <dir>   # 覆盖项目根
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from _common import PROJECT_ROOT


def main() -> int:
    parser = argparse.ArgumentParser(
        description="一次性刷新 STATE.json + task_graph.json"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="项目根目录",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="事件日志路径（默认 .agent-logs/project-events.jsonl）",
    )
    args = parser.parse_args()

    project_root: Path = args.root.resolve()
    template_path = project_root / ".templates" / "STATE.json"
    state_path = project_root / "STATE.json"
    log_path = args.log or (project_root / ".agent-logs" / "project-events.jsonl")
    graph_output = project_root / "task_graph.json"

    from build_state import main_pipeline as build_state_pipeline

    state_result = build_state_pipeline(
        project_root=project_root,
        log_path=log_path,
        template_path=template_path,
        state_path=state_path,
    )
    print(f"[refresh_state] build_state → {state_result}")

    from build_task_graph import build_graph, write_graph

    graph = build_graph(project_root)
    write_graph(graph, graph_output)
    s = graph["summary"]
    print(
        f"[refresh_state] build_task_graph → {s['phase_count']} phases, "
        f"{s['task_count']} tasks, {s['edge_count']} edges → {graph_output}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
