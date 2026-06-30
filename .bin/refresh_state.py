"""
refresh_state.py — 一次性刷新 STATE.json + task_graph.json

合并原 build_state.py + build_task_graph.py 为单一入口，
将 orchestrator 每轮的 bash 调用从 3 次降为 1 次，
减少 agent 上下文消耗和"中途停住"的概率。

用法：
  python scripts/refresh_state.py                # 默认项目根
  python scripts/refresh_state.py --root <dir>   # 覆盖项目根
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Windows 中文终端编码兜底
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_NAME = "task_graph.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="一次性刷新 STATE.json + task_graph.json"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_PROJECT_ROOT,
        help="项目根目录",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="事件日志路径（默认 .agent-logs/latest-project-events.jsonl）",
    )
    parser.add_argument(
        "--task-graph-output",
        type=Path,
        default=None,
        help=f"task_graph.json 输出路径，默认={{root}}/{DEFAULT_OUTPUT_NAME}",
    )
    args = parser.parse_args()

    project_root: Path = args.root.resolve()
    template_path = project_root / ".templates" / "STATE.json"
    state_path = project_root / "STATE.json"
    log_path = args.log or (project_root / ".agent-logs" / "latest-project-events.jsonl")
    graph_output = (args.task_graph_output or project_root / DEFAULT_OUTPUT_NAME).resolve()

    # ── 1. build_state ──
    from build_state import main_pipeline as build_state_pipeline

    state_result = build_state_pipeline(
        project_root=project_root,
        log_path=log_path,
        template_path=template_path,
        state_path=state_path,
    )
    print(f"[refresh_state] build_state → {state_result}")

    # ── 2. build_task_graph ──
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
