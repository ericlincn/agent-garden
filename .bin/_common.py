"""_common.py — build_state / build_task_graph 共享的目录扫描与路径工具。

统一 phase / task 命名正则与遍历逻辑，避免两脚本漂移导致 STATE 与依赖图节点不一致。
命名规范以 AGENT.md 为准：
  - Phase 目录：phase-<零填充两位>-<名称>（suffix 必选）
  - Task 文件：TASK-<零填充三位>-<描述>.md
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

# Windows 中文终端编码兜底
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# phase-NN-<name>：suffix 必选，与 AGENT.md 规范一致
PHASE_DIR_RE = re.compile(r"phase-(\d{2})-([^/\\]+)")
TASK_FILE_RE = re.compile(r"TASK-(\d{3})")

# YAML 前注记解析
FRONTMATTER_RE = re.compile(r"^\ufeff?---\s*\n(.*?)\n---\s*\n", re.DOTALL)
KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")


def list_phases(phases_dir: Path) -> list[tuple[int, str, Path]]:
    """返回 [(phase_num, suffix, phase_dir), ...]，按 phase_num 升序。

    suffix 是 phase-NN- 之后的目录名部分（如 '核心游戏引擎'）。
    不匹配 PHASE_DIR_RE 的目录忽略（含无名称的 phase-NN/）。
    """
    if not phases_dir.exists():
        return []
    result: list[tuple[int, str, Path]] = []
    for entry in sorted(phases_dir.iterdir()):
        if not entry.is_dir():
            continue
        m = PHASE_DIR_RE.match(entry.name)
        if not m:
            continue
        result.append((int(m.group(1)), m.group(2), entry))
    result.sort(key=lambda x: x[0])
    return result


def list_tasks(task_dir: Path) -> list[tuple[str, Path]]:
    """返回 [(task_id, task_path), ...]，按 task_id 升序。

    task_id 形如 'TASK-001'。不匹配 TASK_FILE_RE 的 .md 文件忽略。
    """
    if not task_dir.exists():
        return []
    result: list[tuple[str, Path]] = []
    for entry in sorted(task_dir.iterdir()):
        if not entry.is_file() or not entry.name.endswith(".md"):
            continue
        m = TASK_FILE_RE.match(entry.name)
        if not m:
            continue
        task_id = f"TASK-{m.group(1)}"
        result.append((task_id, entry))
    return result


def normalize_path(raw: str, project_root: Path) -> str:
    """统一为相对 project_root 的正斜杠路径。绝对路径也转相对。"""
    if not raw:
        return raw
    p = raw.replace("\\", "/")
    root = str(project_root).replace("\\", "/").rstrip("/")
    if p.startswith(root + "/"):
        p = p[len(root) + 1:]
    if not os.path.isabs(p):
        return p
    try:
        p = os.path.relpath(p, root).replace("\\", "/")
    except ValueError:
        print(
            f"警告：路径 {raw} 不在项目根 {root} 下，保留原样",
            file=sys.stderr,
        )
    return p


def extract_phase(raw_path: str) -> tuple[int | None, str | None]:
    """从路径提取 (phase_num, suffix)。"""
    m = PHASE_DIR_RE.search(raw_path)
    if not m:
        return None, None
    return int(m.group(1)), m.group(2)


def extract_task_id(raw_path: str) -> str | None:
    m = TASK_FILE_RE.search(raw_path)
    return f"TASK-{m.group(1)}" if m else None


def parse_frontmatter(text: str) -> dict[str, str]:
    """极简 frontmatter 解析：--- 包裹的 YAML 片段，识别顶层 key 与单行列表。

    返回值示例：
    {"task-id": "TASK-001", "dependencies": "[\"phase-01/TASK-001\"]"}
    列表值（- item 格式）以 | 拼接："TASK-001|TASK-002"
    """
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
