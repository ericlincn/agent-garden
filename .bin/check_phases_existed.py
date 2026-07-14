"""
check_phases_existed.py — 检测 phases/ 下是否已有 phase 目录

输出: true / false （纯字符串，不带换行符以外的额外内容）

用于 orchestrator Step 3-1 的 Glob 扫描替代，避免直接走文件系统 glob。
"""
from __future__ import annotations

import sys
from pathlib import Path
from _common import PROJECT_ROOT
PHASES_DIR = PROJECT_ROOT / "phases"


def phases_existed() -> bool:
    if not PHASES_DIR.is_dir():
        return False
    for entry in PHASES_DIR.iterdir():
        if entry.is_dir() and entry.name.startswith("phase-"):
            return True
    return False


if __name__ == "__main__":
    print("true" if phases_existed() else "false")
