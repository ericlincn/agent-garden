"""
check_content_changed.py — 计算 specs/（仅 planner 相关文件）和 discoveries/ 的 SHA-256 hash，
统一记录到 .content_hashes.json。

specs hash 仅覆盖影响 planner 任务生成的文件：
  - specs/design.md
  - specs/** /spec.md（所有 capability spec）
  - specs/contracts/architecture.yaml
  - specs/contracts/routes.yaml
以下文件变更不触发 planner：proposal.md、acceptance.yaml、data.yaml、runtime.yaml

discoveries hash 覆盖 discoveries/ 全部文件。

.content_hashes.json 结构：
{
  "specs":       "<sha256>",
  "discoveries": "<sha256>",
  "last_check":  "2026-07-07T22:00:00"
}

用法：
    python check_content_changed.py --check   输出 [specs] / [discoveries] / 组合 / []（表示未变）
    python check_content_changed.py --save    计算当前 hash 并写入 .content_hashes.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from _common import PROJECT_ROOT

SPECS_DIR = PROJECT_ROOT / "specs"
DISCOVERIES_DIR = PROJECT_ROOT / "discoveries"
HASH_FILE = PROJECT_ROOT / ".content_hashes.json"

PLANNING_CONTRACT_FILES = ("architecture.yaml", "routes.yaml")


def _calculate_specs_planning_hash() -> str:
    """只对影响 planner 任务生成的文件做 hash。"""
    hasher = hashlib.sha256()
    if not SPECS_DIR.is_dir():
        return hasher.hexdigest()

    design_md = SPECS_DIR / "design.md"
    if design_md.is_file():
        hasher.update(b"design.md")
        hasher.update(design_md.read_bytes().replace(b"\r\n", b"\n"))

    for spec_md in sorted(SPECS_DIR.rglob("spec.md")):
        rel_path = spec_md.relative_to(SPECS_DIR)
        hasher.update(str(rel_path).encode("utf-8"))
        hasher.update(spec_md.read_bytes().replace(b"\r\n", b"\n"))

    contracts_dir = SPECS_DIR / "contracts"
    if contracts_dir.is_dir():
        for name in sorted(PLANNING_CONTRACT_FILES):
            contract_file = contracts_dir / name
            if contract_file.is_file():
                hasher.update(name.encode("utf-8"))
                hasher.update(contract_file.read_bytes().replace(b"\r\n", b"\n"))

    return hasher.hexdigest()


def _calculate_dir_hash(directory: Path) -> str:
    """全量目录 hash，用于 discoveries/。"""
    hasher = hashlib.sha256()
    if not directory.is_dir():
        return hasher.hexdigest()
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for file in sorted(files):
            file_path = Path(root) / file
            rel_path = file_path.relative_to(directory)
            hasher.update(str(rel_path).encode("utf-8"))
            hasher.update(file_path.read_bytes().replace(b"\r\n", b"\n"))
    return hasher.hexdigest()


def _read_saved_hashes() -> dict:
    if not HASH_FILE.exists():
        return {}
    try:
        raw = HASH_FILE.read_text(encoding="utf-8")
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_saved_hashes(specs_hash: str, discoveries_hash: str) -> None:
    data = {"specs": specs_hash, "discoveries": discoveries_hash}
    data["last_check"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    HASH_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _is_changed(target: str, saved: dict, current_hash: str) -> bool:
    saved_hash = saved.get(target)
    if not isinstance(saved_hash, str):
        return True
    return current_hash != saved_hash


def main() -> int:
    parser = argparse.ArgumentParser(
        description="计算 specs/（planner 相关子集）和 discoveries/ 的 SHA-256 hash"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="比较 hash，输出 [specs] / [discoveries] / []")
    group.add_argument("--save", action="store_true", help="计算当前 hash 并写入 .content_hashes.json")
    args = parser.parse_args()

    if args.check:
        out: list[str] = []

        if not SPECS_DIR.is_dir():
            print("Error: specs directory not found", file=sys.stderr)
            return 1
        specs_hash = _calculate_specs_planning_hash()
        saved = _read_saved_hashes()
        if _is_changed("specs", saved, specs_hash):
            out.append("specs")

        if DISCOVERIES_DIR.is_dir():
            discoveries_hash = _calculate_dir_hash(DISCOVERIES_DIR)
            if _is_changed("discoveries", saved, discoveries_hash):
                out.append("discoveries")

        print(json.dumps(out))

    elif args.save:
        specs_hash = _calculate_specs_planning_hash() if SPECS_DIR.is_dir() else ""
        discoveries_hash = _calculate_dir_hash(DISCOVERIES_DIR) if DISCOVERIES_DIR.is_dir() else ""
        _write_saved_hashes(specs_hash, discoveries_hash)

    return 0


if __name__ == "__main__":
    sys.exit(main())
