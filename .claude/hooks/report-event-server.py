# .claude/hooks/report_event_server.py
"""
Agent Garden 事件报告 MCP Server
负责：文件后缀修正、结构化日志记录、STATE.json 增量更新
"""
import json
import os
import re
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="Agent Event Reporter")

VALID_EVENTS = [
    "TASK_PLAN_COMPLETED", "TDD_COMPLETED",
    "REVIEW_COMPLETED", "REVIEW_FAILED",
    "TEST_COMPLETED", "TEST_FAILED"
]

EVENT_SUFFIX_MAP = {
    "TDD_COMPLETED":      ".done.md",
    "REVIEW_COMPLETED":   ".done.md",
    "REVIEW_FAILED":      ".blocked.md",
    "TEST_COMPLETED":     ".done.md",
    "TEST_FAILED":        ".blocked.md",
}

PROJECT_ROOT = os.environ.get("CLAUDE_PROJECT_DIR", ".")
LOG_FILE = os.path.join(PROJECT_ROOT, ".claude-logs", "agent-events.jsonl")
STATE_FILE = os.path.join(PROJECT_ROOT, "STATE.json")

# 确保日志目录存在
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def safe_join(root: str, path: str) -> str:
    full = os.path.normpath(os.path.join(root, path))
    if not full.startswith(os.path.normpath(root)):
        raise ValueError(f"路径越界: {path}")
    return full


def extract_task_id(task_path: str) -> str:
    """从任务文件路径中提取任务ID，如 TASK-001"""
    m = re.search(r'(TASK-\d+)', task_path)
    return m.group(1) if m else ""


def extract_phase_id(task_path: str) -> str:
    """从路径提取 phase-XX（不含名称后缀），如 phase-01"""
    m = re.search(r'(phase-\d+)', task_path)
    return m.group(1) if m else ""


def extract_task_suffix(task_path: str) -> str:
    """返回当前文件后缀，如 .todo.md，若未找到返回空"""
    m = re.search(r'\.(todo|doing|done|blocked)\.md$', task_path)
    return f".{m.group(1)}.md" if m else ""


def correct_suffix_and_rename(task_path: str, event_type: str) -> str:
    """根据事件类型修正文件后缀并重命名，返回修正后路径"""
    expected_suffix = EVENT_SUFFIX_MAP.get(event_type)
    if not expected_suffix:
        return task_path

    corrected_path = re.sub(r'\.(todo|doing|done|blocked)\.md$', expected_suffix, task_path)
    if corrected_path == task_path:
        return task_path

    old_full = safe_join(PROJECT_ROOT, task_path)
    new_full = safe_join(PROJECT_ROOT, corrected_path)

    if os.path.exists(old_full):
        if os.path.exists(new_full):
            os.remove(new_full)
        os.rename(old_full, new_full)
        return corrected_path
    else:
        return task_path


def write_event_log(entry: dict):
    """将一条结构化事件追加到 JSONL 日志"""
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        **entry
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def calculate_retry_count(task_id: str) -> int:
    """从日志中统计某任务累计的 REVIEW_FAILED 与 TEST_FAILED 次数"""
    if not os.path.exists(LOG_FILE):
        return 0
    count = 0
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("task_id") == task_id and \
                   entry.get("event_type") in ("REVIEW_FAILED", "TEST_FAILED"):
                    count += 1
            except json.JSONDecodeError:
                continue
    return count


def update_state_json(event_type: str, agent_name: str, task_path: str, new_suffix: str, retry_count: int):
    """
    根据事件更新 STATE.json 中的任务状态、Phase 统计、全局时间。
    如果 STATE.json 不存在则跳过。
    """
    if not os.path.exists(STATE_FILE):
        return

    task_id = extract_task_id(task_path)
    phase_id = extract_phase_id(task_path)
    if not task_id or not phase_id:
        return

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            state = json.load(f)
        except json.JSONDecodeError:
            return

    now = time.strftime("%Y-%m-%dT%H:%M:%S")

    # 确保 phases 和对应 phase 存在
    if "phases" not in state or phase_id not in state["phases"]:
        return

    phase = state["phases"][phase_id]
    if "tasks" not in phase:
        phase["tasks"] = {}

    # 更新 task（如果不存在则创建基本条目）
    if task_id not in phase["tasks"]:
        phase["tasks"][task_id] = {
            "description": "",
            "suffix": ".todo.md",
            "dependencies": [],
            "retries": 0,
            "last_event": None,
            "last_agent": None,
            "updated_at": None
        }

    task = phase["tasks"][task_id]
    task["suffix"] = new_suffix
    task["retries"] = retry_count
    task["last_event"] = event_type
    task["last_agent"] = agent_name
    task["updated_at"] = now

    # 重新计算该 phase 的统计
    done = doing = blocked = 0
    for t in phase["tasks"].values():
        s = t.get("suffix", "")
        if s == ".done.md":
            done += 1
        elif s == ".doing.md":
            doing += 1
        elif s == ".blocked.md":
            blocked += 1

    total_tasks = len(phase["tasks"])
    # 判断 phase 状态
    if done == total_tasks and total_tasks > 0:
        phase["status"] = "已完成"
    elif blocked > 0 or doing > 0 or done > 0:
        phase["status"] = "进行中"
    else:
        phase["status"] = "未开始"

    phase["updated_at"] = now

    # 重新计算全局统计
    total_phases = len(state["phases"])
    completed = sum(1 for p in state["phases"].values() if p.get("status") == "已完成")
    active = total_phases - completed

    state["last_updated"] = now
    state["total_phases"] = total_phases
    state["completed_phases"] = completed
    state["active_phases"] = active

    # 原子写入
    tmp_path = STATE_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, STATE_FILE)


@mcp.tool()
def report_event(event_type: str, agent_name: str, payload: dict = None) -> str:
    """Subagent 完成任务后调用此工具生成标准事件块，同时更新文件后缀、日志和 STATE.json"""
    if event_type not in VALID_EVENTS:
        return json.dumps({
            "error": f"无效事件类型: {event_type}. 允许的类型: {VALID_EVENTS}"
        }, ensure_ascii=False)

    if payload is None:
        payload = {}

    # 提取路径键
    path_key = None
    if "task_path" in payload:
        path_key = "task_path"
    elif "plan_path" in payload:
        path_key = "plan_path"

    old_suffix = ""
    new_suffix = ""
    corrected_path = ""

    # 需要后缀修正的事件
    if path_key and event_type in EVENT_SUFFIX_MAP:
        old_path = payload[path_key]
        old_suffix = extract_task_suffix(old_path)
        corrected_path = correct_suffix_and_rename(old_path, event_type)
        new_suffix = extract_task_suffix(corrected_path)
        payload[path_key] = corrected_path
    else:
        corrected_path = payload.get(path_key, "")

    task_id = extract_task_id(corrected_path) if path_key else ""
    # 重试次数统计
    retry_count = calculate_retry_count(task_id) if task_id else 0

    # 构建事件对象
    event_obj = {
        "_mcp_called": True,
        "agent": agent_name,
        "event": event_type,
        "payload": payload
    }

    # 写入结构化日志
    write_event_log({
        "agent_name": agent_name,
        "event_type": event_type,
        "task_id": task_id,
        "task_path": corrected_path,
        "phase_id": extract_phase_id(corrected_path),
        "previous_suffix": old_suffix,
        "new_suffix": new_suffix,
        "retry_count": retry_count,
    })

    # 更新 STATE.json（仅对会改变任务后缀的事件）
    if event_type in EVENT_SUFFIX_MAP and corrected_path:
        update_state_json(
            event_type=event_type,
            agent_name=agent_name,
            task_path=corrected_path,
            new_suffix=new_suffix,
            retry_count=retry_count
        )

    return f"```event\n{json.dumps(event_obj, ensure_ascii=False, indent=2)}\n```"


if __name__ == "__main__":
    mcp.run()