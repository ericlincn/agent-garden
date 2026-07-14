"""
get_discoveries_list.py — 列出 discoveries/ 中匹配条件的发现文件路径

条件：status: open 且 severity: high/critical 且 phase == 当前 phase。

用于 orchestrator / schedule.py 获取需处理的 discovery 文件列表。

用法：
    python .bin/get_discoveries_list.py --phase phase-03   # 仅某 phase
    python .bin/get_discoveries_list.py                     # 全部 phase

输出：stdout — 每行一个发现文件的相对路径（如 discoveries/DISC-001.md）
      空输出表示无匹配发现。
退出码：0 正常，1 错误。
"""
from __future__ import annotations

import argparse
import sys

from _common import PROJECT_ROOT, parse_frontmatter

DISCOVERIES_DIR = PROJECT_ROOT / "discoveries"


def list_matching(phase: str | None = None) -> list[str]:
    if not DISCOVERIES_DIR.is_dir():
        return []

    phase_prefix = phase if phase is None else (phase if phase.startswith("phase-") else f"phase-{phase}")
    results: list[str] = []

    for entry in sorted(DISCOVERIES_DIR.iterdir()):
        if not entry.is_file() or not entry.name.endswith(".md"):
            continue
        try:
            fm = parse_frontmatter(entry.read_text(encoding="utf-8"))
        except OSError:
            continue

        if fm.get("status") != "open":
            continue
        if fm.get("severity") not in ("high", "critical"):
            continue
        if phase_prefix is not None and fm.get("phase") != phase_prefix:
            continue
        results.append(str(entry.relative_to(PROJECT_ROOT)).replace("\\", "/"))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="列出 discoveries/ 中匹配条件的发现文件路径")
    parser.add_argument("--phase", default=None, help="phase 标识，如 phase-03 或 03（不传则匹配全部 phase）")
    args = parser.parse_args()

    paths = list_matching(args.phase)
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
