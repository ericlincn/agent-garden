"""
build_task_graph.py — 遍历 phases/ 目录，生成 task 之间依赖关系图 JSON

数据源：
  phases/phase-XX-<name>/tasks/TASK-NNN-*.md 的 frontmatter dependencies 字段

输出 {root}/task_graph.json，结构：
  {
    "phases": [ {id, task_count}, ... ],                      # 按 phase 序号升序
    "nodes": [
      {
        "id": "phase-01/TASK-001",                            # 全局唯一
        "phase": "phase-01",
        "task_id": "TASK-001",
        "dependencies": ["phase-01/TASK-002"],                # 解析后的全 id
        "dependents": ["phase-01/TASK-003"]                   # 反向
      }, ...
    ],
    "edges": [ {from, to}, ... ],                              # from=依赖方，to=被依赖方
    "summary": { phase_count, task_count, edge_count }
  }

依赖解析规则：
  - dependencies 中的 TASK-NNN 默认在【同一 phase】内解析
  - 同 phase 找不到时，按 phase 序号升序兜底查找
  - 仍找不到时：stderr 警告并跳过该边
  - 同一对 (from, to) 边去重

用法：
  python build_task_graph.py                       # 默认：根=脚本目录
  python build_task_graph.py --root <dir>          # 覆盖项目根
  python build_task_graph.py --output <file>       # 覆盖输出路径
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from _common import (
    PHASE_DIR_RE,
    TASK_FILE_RE,
    list_phases,
    list_tasks,
)

# Windows 中文终端编码兜底
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_NAME = "task_graph.json"

# 兼容 UTF-8 BOM（\ufeff）和无 BOM 两种情形
FRONTMATTER_RE = re.compile(r"^\ufeff?---\s*\n(.*?)\n---\s*\n", re.DOTALL)
KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")

# phase-NN/TASK-NNN 跨 phase 依赖，如 "phase-01/TASK-001"
CROSS_PHASE_DEP_RE = re.compile(r"^phase-(\d{2})/TASK-(\d{3})$")


# ───────────────────────── 解析工具 ─────────────────────────

def parse_frontmatter(text: str) -> dict[str, str]:
    """极简 frontmatter 解析：--- 包裹的 YAML 片段，识别顶层 key 与单行列表。"""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    result: dict[str, str] = {}
    current_list_key: str | None = None
    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("- "):
            if current_list_key is None:
                continue
            result[current_list_key] = (
                result.get(current_list_key, "") + "|" + line.lstrip()[2:].strip()
            ).strip("|")
            continue
        kv = KV_RE.match(line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2).strip()
        if value == "" or value.startswith("[") or value.startswith("{"):
            current_list_key = key
            result[key] = value
        else:
            current_list_key = None
            result[key] = value
    return result


def parse_dependencies(value: str) -> list[str]:
    """兼容 YAML 数组 []、JSON 数组 []、列表 - TASK-001 等。"""
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


# ───────────────────────── 目录扫描 ─────────────────────────
# list_phases / list_tasks / PHASE_DIR_RE / TASK_FILE_RE 由 _common 统一提供


def read_dependencies(task_path: Path) -> list[str]:
    """从 task frontmatter 读 dependencies 列表；失败 / 缺字段时返回 []。"""
    try:
        text = task_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"[build_task_graph] 读取失败 {task_path}: {e}", file=sys.stderr)
        return []
    fm = parse_frontmatter(text)
    return parse_dependencies(fm.get("dependencies", ""))


# ───────────────────────── 图构建 ─────────────────────────

def build_graph(project_root: Path) -> dict[str, Any]:
    """构造完整图数据结构。"""
    phases = list_phases(project_root / "phases")

    # 全局 (task_id → [phase_id, ...]) 索引，供跨 phase 解析
    global_index: dict[str, list[str]] = {}
    phases_meta: list[dict[str, Any]] = []
    raw_nodes: list[dict[str, Any]] = []

    for phase_num, _phase_name, phase_dir in phases:
        phase_id = f"phase-{phase_num:02d}"
        tasks = list_tasks(phase_dir / "tasks")
        for task_id, task_path in tasks:
            dependencies = read_dependencies(task_path)
            global_index.setdefault(task_id, []).append(phase_id)
            raw_nodes.append(
                {
                    "id": f"{phase_id}/{task_id}",
                    "phase": phase_id,
                    "task_id": task_id,
                    "_deps": dependencies,
                }
            )
        phases_meta.append(
            {
                "id": phase_id,
                "task_count": len(tasks),
            }
        )

    # 解析依赖边：from = 依赖方，to = 被依赖方
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    resolved_deps: dict[str, list[str]] = {}

    # 快速 phase ID 集合，用于验证跨 phase 依赖
    all_phase_ids = {p["id"] for p in phases_meta}
    # 快速 node ID 集合，用于验证 task 存在
    all_node_ids = {n["id"] for n in raw_nodes}

    for node in raw_nodes:
        my_id = node["id"]
        my_phase = node["phase"]
        deps_out: list[str] = []
        for raw in node["_deps"]:
            # 尝试解析跨 phase 依赖：phase-NN/TASK-NNN
            xm = CROSS_PHASE_DEP_RE.match(raw)
            if xm:
                target_phase = f"phase-{xm.group(1)}"
                dep_task_id = f"TASK-{xm.group(2)}"
                chosen = f"{target_phase}/{dep_task_id}"
                if target_phase not in all_phase_ids:
                    print(
                        f"[build_task_graph] 依赖 phase '{target_phase}' 不存在"
                        f"（来自 {my_id}）",
                        file=sys.stderr,
                    )
                    continue
                if chosen not in all_node_ids:
                    print(
                        f"[build_task_graph] 依赖 '{raw}' 不存在"
                        f"（来自 {my_id}）",
                        file=sys.stderr,
                    )
                    continue
                deps_out.append(chosen)
                edge = (my_id, chosen)
                if edge not in seen:
                    seen.add(edge)
                    edges.append({"from": my_id, "to": chosen})
                continue

            # 同 phase / 兜底：TASK-NNN
            m = TASK_FILE_RE.match(raw)
            if not m:
                print(
                    f"[build_task_graph] 跳过非法依赖 '{raw}'（来自 {my_id}）",
                    file=sys.stderr,
                )
                continue
            dep_task_id = f"TASK-{m.group(1)}"
            candidates = global_index.get(dep_task_id, [])
            chosen: str | None = None
            # 同 phase 优先
            for cand_phase in candidates:
                if cand_phase == my_phase:
                    chosen = f"{cand_phase}/{dep_task_id}"
                    break
            # 跨 phase 兜底（按 phase 序号升序的第一项）
            if chosen is None and candidates:
                chosen = f"{candidates[0]}/{dep_task_id}"
            if chosen is None:
                print(
                    f"[build_task_graph] 依赖 '{raw}' 不存在（来自 {my_id}）",
                    file=sys.stderr,
                )
                continue
            deps_out.append(chosen)
            edge = (my_id, chosen)
            if edge not in seen:
                seen.add(edge)
                edges.append({"from": my_id, "to": chosen})
        resolved_deps[my_id] = deps_out

    # 反向索引（dependents）
    dependents_map: dict[str, list[str]] = {n["id"]: [] for n in raw_nodes}
    for src, dst in seen:
        dependents_map[dst].append(src)
    for k in dependents_map:
        dependents_map[k].sort()

    final_nodes = [
        {
            "id": n["id"],
            "phase": n["phase"],
            "task_id": n["task_id"],
            "dependencies": resolved_deps[n["id"]],
            "dependents": dependents_map[n["id"]],
        }
        for n in raw_nodes
    ]

    edges.sort(key=lambda e: (e["from"], e["to"]))

    return {
        "phases": phases_meta,
        "nodes": final_nodes,
        "edges": edges,
        "summary": {
            "phase_count": len(phases_meta),
            "task_count": len(final_nodes),
            "edge_count": len(edges),
        },
    }


def write_graph(graph: dict[str, Any], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="遍历 phases/ 目录生成 task 依赖关系图 JSON",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_PROJECT_ROOT,
        help="项目根目录（影响 phases/ 扫描与默认输出位置），默认=脚本所在目录",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"输出 JSON 路径，默认={{root}}/{DEFAULT_OUTPUT_NAME}",
    )
    args = parser.parse_args()

    project_root: Path = args.root.resolve()
    output_path: Path = (args.output or project_root / DEFAULT_OUTPUT_NAME).resolve()

    graph = build_graph(project_root)
    write_graph(graph, output_path)

    s = graph["summary"]
    print(
        f"[build_task_graph] {s['phase_count']} phases, "
        f"{s['task_count']} tasks, {s['edge_count']} edges → {output_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
