"""
get_discoveries_count.py — 统计 discoveries/ 中匹配条件的发现数量

用于 orchestrator Step 5 Explorer 调度中的判断：
  "读 discoveries/ 中 status: open 且 severity: high/critical 且 phase == 当前 phase 的数量"

用法：
    python .bin/get_discoveries_count.py --phase phase-03
    python .bin/get_discoveries_count.py --phase 03

输出：纯数字（如 0 / 2 / 5），不包含换行符以外的额外内容。
退出码：0 正常，1 错误。
"""
from __future__ import annotations

import argparse
import sys

from _common import PROJECT_ROOT, parse_frontmatter

DISCOVERIES_DIR = PROJECT_ROOT / "discoveries"


def count_matching(phase: str) -> int:
    if not DISCOVERIES_DIR.is_dir():
        return 0

    # 兼容 "phase-03" 和 "03" 两种输入
    phase_prefix = phase if phase.startswith("phase-") else f"phase-{phase}"
    count = 0

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
        if fm.get("phase") != phase_prefix:
            continue
        count += 1

    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="统计 discoveries/ 中匹配条件的发现数量")
    parser.add_argument("--phase", required=True, help="phase 标识，如 phase-03 或 03")
    args = parser.parse_args()

    count = count_matching(args.phase)
    print(count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
