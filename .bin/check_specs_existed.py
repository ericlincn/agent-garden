"""
check_specs_existed.py — 检查 specs/ 是否存在且含有效文件

用于 produce-specs SKILL.md Step 2 的文件夹检查替代：
  - 存在且含文件（至少一个 .md 或 .yaml）→ "update"（对应 Update 模式）
  - 不存在或为空                      → "create"（对应 Create 模式）

输出：update / create （纯字符串，无额外内容）
退出码：0 正常
"""
from __future__ import annotations

import sys
from pathlib import Path
from _common import PROJECT_ROOT
SPECS_DIR = PROJECT_ROOT / "specs"

VALID_EXTENSIONS = {".md", ".yaml", ".yml"}


def check() -> str:
    if not SPECS_DIR.is_dir():
        return "create"
    for entry in SPECS_DIR.iterdir():
        if entry.is_file() and entry.suffix.lower() in VALID_EXTENSIONS:
            return "update"
    return "create"


if __name__ == "__main__":
    print(check())
