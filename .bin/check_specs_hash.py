"""
check_specs_hash.py — 计算 specs/ 目录全部内容的 SHA-256 总 hash

用法：
    python check_specs_hash.py --check   计算 hash 并与 .specs_hash.txt 比较，输出 true/false
    python check_specs_hash.py --save    计算 hash 并写入 .specs_hash.txt
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = PROJECT_ROOT / "specs"
HASH_FILE = PROJECT_ROOT / ".specs_hash.txt"


def calculate_specs_hash(specs_dir: Path) -> str:
    hasher = hashlib.sha256()

    for root, dirs, files in os.walk(specs_dir):
        dirs.sort()
        for file in sorted(files):
            file_path = Path(root) / file
            rel_path = file_path.relative_to(specs_dir)
            hasher.update(str(rel_path).encode("utf-8"))
            hasher.update(file_path.read_bytes().replace(b"\r\n", b"\n"))

    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="计算 specs/ 目录全部内容的 SHA-256 总 hash"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="比较 hash，输出 true=未变 / false=已变")
    group.add_argument("--save", action="store_true", help="计算 hash 并写入 .specs_hash.txt")
    args = parser.parse_args()

    if not SPECS_DIR.is_dir():
        print(f"Error: specs directory not found at {SPECS_DIR}", file=sys.stderr)
        return 1

    current_hash = calculate_specs_hash(SPECS_DIR)

    if args.check:
        if not HASH_FILE.exists():
            print("false")
            return 0
        saved_hash = HASH_FILE.read_text(encoding="utf-8").strip()
        print("true" if current_hash == saved_hash else "false")

    elif args.save:
        HASH_FILE.write_text(current_hash + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
