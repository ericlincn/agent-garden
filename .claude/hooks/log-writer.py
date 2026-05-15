#!/usr/bin/env python
# .claude/hooks/log-writer.py
# 简化版：仅记录 Subagent 启动/停止和工具调用。
# 事件性日志已由 report-event MCP 统一处理，写入 agent-events.jsonl

import sys, json, os, time, re

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.environ.get("CLAUDE_PROJECT_DIR", ".")
LOG_FILE = os.path.join(PROJECT_ROOT, ".claude-logs", "agent-events.jsonl")


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception:
        return sys.exit(1)

    event = data.get("hook_event_name", "Unknown")
    agent = data.get("agent_type", "Unknown").capitalize()
    session = data.get("session_id", "unknown")
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

    log_entry = {
        "timestamp": timestamp,
        "agent_name": agent,
        "event_type": f"HOOK_{event.upper()}",
        "session_id": str(session)[:8],
    }

    if event == "PreToolUse":
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        log_entry["event_type"] = "TOOL_CALL"
        log_entry["payload"] = {
            "tool_name": tool_name,
            "tool_input_summary": str(tool_input)[:200]
        }
    else:
        log_entry["message"] = str(data.get("last_assistant_message"))[:100]

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    sys.exit(0)


if __name__ == "__main__":
    main()