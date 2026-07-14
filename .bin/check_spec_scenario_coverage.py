#!/usr/bin/env python3
"""check_spec_scenario_coverage.py — 检查 specs 中全部 Scenario 是否被 task 的 spec_ref 覆盖

检查项：
    1. 提取 specs/<capability>/spec.md 中全部 Scenario，构造 S_all
    2. 提取 phases/phase-*/tasks/TASK-*.md 中 ## 验收标准 下的 spec_ref 行，构造 S_covered
    3. 输出 S_uncovered = S_all - S_covered

Scenario 标识格式：<capability>/<requirement_name>/<scenario_name>
    - capability = spec.md 所在目录名
    - requirement_name = "### Requirement: <name>" 行的 <name>
    - scenario_name = "#### Scenario: <name>" 行的 <name>

用法：
    python .bin/check_spec_scenario_coverage.py                         # Create 模式：全量扫描 specs/
    python .bin/check_spec_scenario_coverage.py --scenarios "<s1>" "<s2>"  # Update 模式：只检查指定列表

输出：
    stdout — 人类/agent 可读的检查报告（含明确操作指令）
    stderr — 仅致命错误
退出码：0 全覆盖，1 有遗漏或错误。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from _common import PROJECT_ROOT, list_phases, list_tasks, parse_frontmatter

SPECS_DIR = PROJECT_ROOT / "specs"
PHASES_DIR = PROJECT_ROOT / "phases"

REQUIREMENT_RE = re.compile(r"^###\s+Requirement:\s*(.+)$")
SCENARIO_RE = re.compile(r"^####\s+Scenario:\s*(.+)$")
SPEC_REF_RE = re.compile(r"spec_ref:\s*(.+)")


def extract_scenarios_from_spec(spec_path: Path, capability: str) -> set[str]:
    """从单个 spec.md 提取全部 Scenario 标识。

    返回 {"<capability>/<requirement>/<scenario>", ...}
    """
    text = spec_path.read_text(encoding="utf-8")
    scenarios: set[str] = set()
    current_requirement: str | None = None

    for line in text.splitlines():
        m = REQUIREMENT_RE.match(line.strip())
        if m:
            current_requirement = m.group(1).strip()
            continue

        m = SCENARIO_RE.match(line.strip())
        if m and current_requirement:
            scenario_name = m.group(1).strip()
            scenarios.add(f"{capability}/{current_requirement}/{scenario_name}")

    return scenarios


def collect_all_scenarios() -> set[str]:
    """遍历 specs/ 下全部 capability 目录，提取全部 Scenario。"""
    all_scenarios: set[str] = set()
    if not SPECS_DIR.is_dir():
        return all_scenarios

    for entry in sorted(SPECS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        spec_path = entry / "spec.md"
        if not spec_path.exists():
            continue
        all_scenarios.update(extract_scenarios_from_spec(spec_path, entry.name))

    return all_scenarios


def collect_covered_scenarios() -> set[str]:
    """遍历 phases/ 下全部 task 文件，提取 spec_ref 引用的 Scenario。"""
    covered: set[str] = set()
    if not PHASES_DIR.is_dir():
        return covered

    for _phase_num, _name, phase_dir in list_phases(PHASES_DIR):
        for _task_id, task_path in list_tasks(phase_dir / "tasks"):
            try:
                text = task_path.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in text.splitlines():
                m = SPEC_REF_RE.search(line.strip())
                if m:
                    covered.add(m.group(1).strip())

    return covered


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Scenario 是否被 task 覆盖")
    parser.add_argument("--scenarios", nargs="+", default=None,
                        help="待检查的 Scenario 列表（Update 模式使用，不传则全量扫描 specs/）")
    args = parser.parse_args()

    if args.scenarios:
        s_all = set(args.scenarios)
    else:
        s_all = collect_all_scenarios()
        if not s_all:
            print("OK — specs/ 下无 Scenario，无需检查")
            return 0

    s_covered = collect_covered_scenarios()
    s_uncovered = s_all - s_covered
    s_orphan = s_covered - s_all if args.scenarios is None else set()

    covered_count = len(s_all & s_covered)
    rate = round(covered_count / len(s_all) * 100, 1)

    if not s_uncovered and not s_orphan:
        print(f"OK — {len(s_all)} 个 Scenario 全部被 task 覆盖（覆盖率 100%）")
        return 0

    lines: list[str] = []
    lines.append(f"Scenario 覆盖率: {covered_count}/{len(s_all)} ({rate}%)")

    if s_uncovered:
        lines.append("")
        lines.append(f"未覆盖的 Scenario（{len(s_uncovered)} 个）— planner 需为以下每条 Scenario 创建或补充 task：")
        for sc in sorted(s_uncovered):
            parts = sc.split("/", 2)
            cap = parts[0] if len(parts) > 0 else "?"
            req = parts[1] if len(parts) > 1 else "?"
            scenario = parts[2] if len(parts) > 2 else "?"
            lines.append(f"  - {sc}")
            lines.append(f"    定义于: specs/{cap}/spec.md 的 Requirement「{req}」下的 Scenario「{scenario}」")
            lines.append(f"    操作: 在对应 phase 的 task 验收标准中追加 spec_ref: {sc}，或新建 task 覆盖")

    if s_orphan:
        lines.append("")
        lines.append(f"孤儿引用（{len(s_orphan)} 个）— task 引用了 specs 中不存在的 Scenario，需修正或删除：")
        for ref in sorted(s_orphan):
            lines.append(f"  - {ref}")
            lines.append(f"    操作: 检查 task 文件中的 spec_ref 行，修正为有效 Scenario 或删除该行")

    print("\n".join(lines))
    return 1


if __name__ == "__main__":
    sys.exit(main())
