#!/usr/bin/env python
# .bin/play_sound.py
"""
用法: python play_sound.py alert|idle
"""

import subprocess
import sys
import os
import random
from datetime import datetime

# 路径设置
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
mpg123_path = os.path.join(script_dir, "mpg123.exe")
log_dir = os.path.join(project_root, ".agent-logs")
log_file = os.path.join(log_dir, "sound.log")

# 音频文件映射
ALERT_FILES = ["gas.mp3", "mineral.mp3", "supply.mp3"]
IDLE_FILES = ["addon.mp3", "research.mp3", "upgrade.mp3"]

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    os.makedirs(log_dir, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    if len(sys.argv) < 2:
        log("错误: 缺少参数，请使用 alert 或 idle")
        sys.exit(1)

    sound_type = sys.argv[1].lower()
    if sound_type not in ("alert", "idle"):
        log(f"错误: 无效参数 '{sound_type}'，请使用 alert 或 idle")
        sys.exit(1)

    # 根据类型选择文件列表
    if sound_type == "alert":
        file_list = ALERT_FILES
    else:  # idle
        file_list = IDLE_FILES

    # 随机选择一个 mp3 文件
    chosen_file = random.choice(file_list)
    mp3_path = os.path.join(script_dir, chosen_file)

    if not os.path.exists(mp3_path):
        log(f"错误: 文件不存在 {mp3_path}")
        sys.exit(1)

    log(f"播放: {chosen_file} (类型: {sound_type})")

    try:
        # Python 启动的 PowerShell 子进程可以正常访问音频
        subprocess.Popen(
            ["powershell", "-Command",
             f"Start-Process -FilePath '{mpg123_path}' -ArgumentList '{mp3_path}' -WindowStyle Hidden"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        log(f"异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()