"""
report-event-server.py — Agent Garden 事件报告 MCP Server

职责：
   1) 写全量事件日志 .agent-logs/agent-events.jsonl
   2) 维护最新事件快照 .agent-logs/latest-project-events.jsonl
   3) PHASE_PLAN_COMPLETED 自动拆分复数数组字段为多条独立事件
   4) 不在 VALID_EVENTS 的事件不写任何日志
"""
from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

# Windows 中文终端编码兜底
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

mcp = FastMCP(name="Agent Event Reporter")

VALID_EVENTS = [
    "SPECS_CREATED", "SPECS_UPDATED",
    "PHASE_PLAN_COMPLETED",
    "TDD_INPROGRESS", "TDD_COMPLETED", "TDD_FAILED",
    "REVIEW_INPROGRESS", "REVIEW_COMPLETED", "REVIEW_FAILED",
    "TEST_INPROGRESS", "TEST_COMPLETED", "TEST_FAILED",
    "HEARTBEAT", "SERVER_STARTED",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(PROJECT_ROOT, ".agent-logs")
FULL_LOG_FILE = os.path.join(LOG_DIR, "agent-events.jsonl")
LATEST_PROJECT_LOG_FILE = os.path.join(LOG_DIR, "latest-project-events.jsonl")

os.makedirs(LOG_DIR, exist_ok=True)

# 单进程串行化锁：所有日志写入持锁后执行，避免并发 append 导致行交错
_LOG_LOCK = threading.Lock()


# ──────────────── 工具函数 ────────────────

def warn(msg: str) -> None:
    print(f"[report-event] WARN: {msg}", file=sys.stderr)


def normalize_path(raw: str) -> str:
    """绝对→相对项目根；反斜杠→正斜杠。"""
    if not raw:
        return raw
    p = raw.replace("\\", "/")
    root = str(PROJECT_ROOT).replace("\\", "/").rstrip("/")
    if p.startswith(root + "/"):
        p = p[len(root) + 1:]
    if not os.path.isabs(p):
        return p
    try:
        p = os.path.relpath(p, root).replace("\\", "/")
    except ValueError:
        warn(f"路径 {raw} 不在项目根 {root} 下，保留原样")
    return p


def normalize_payload_paths(payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    """就地规范化 payload 中指定字段的路径。"""
    for f in fields:
        if f in payload and isinstance(payload[f], str):
            payload[f] = normalize_path(payload[f])


def now_iso_ms() -> str:
    """毫秒精度 ISO-8601 时间戳，如 2026-06-21T14:30:15.123"""
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


def append_jsonl(path: str, entry: dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()


# ──────────────── 复数数组字段拆分 ────────────────

def split_plural_field(
    entry: dict[str, Any],
    *,
    single: str,
    plural: str,
    accompaniments: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """复数数组字段兜底拆分，适用于任何事件类型。

    - 优先 single 字段（非空时直接返回 [entry]）
    - 数组形式：按 plural 顺序拆为多条独立事件，每条只带单个值
    - accompaniments: {plural_field: single_field}，如 {"task_folders": "task_folder"}
      指定伴随数组字段及其对应的单数名，按相同下标配对
    - 每条新事件 timestamp / agent_name / event_type 沿用原 entry
    - payload 中的标量字段（str/int/float/bool/None）仅首条携带，避免重复
    - 数组字段（plural 及其 accompaniments）不在新 payload 中出现
    """
    payload = entry.get("payload") or {}
    if payload.get(single):
        return [entry]
    items = payload.get(plural) or []
    if not items:
        return [entry]

    all_plural_fields = {plural}
    if accompaniments:
        all_plural_fields.update(accompaniments.keys())

    out: list[dict[str, Any]] = []
    scalars_included = False
    for i in range(len(items)):
        new_payload: dict[str, Any] = {single: items[i]}
        if accompaniments:
            for p_field, s_field in accompaniments.items():
                arr = payload.get(p_field) or []
                new_payload[s_field] = arr[i] if i < len(arr) else None
        if not scalars_included:
            for k, v in payload.items():
                if k in all_plural_fields:
                    continue
                if isinstance(v, (str, int, float, bool)) or v is None:
                    new_payload[k] = v
            scalars_included = True
        out.append({**entry, "payload": new_payload})
    return out


# ──────────────── MCP 工具入口 ────────────────

@mcp.tool()
def report_event(event_type: str, agent_name: str, payload: dict = None):
    if payload is None:
        payload = {}

    if event_type not in VALID_EVENTS:
        msg = f"[report-event] 非法 event_type '{event_type}'，合法值: {VALID_EVENTS}。事件未写入日志。"
        print(msg, file=sys.stderr)
        return {"ok": False, "error": msg}

    # 规范化所有路径字段
    normalize_payload_paths(payload, ("task_path", "plan_path", "task_folder", "specs_folder", "references_folder"))

    log_entry = {
        "timestamp": now_iso_ms(),
        "agent_name": agent_name.capitalize(),
        "event_type": event_type,
        "payload": payload,
    }

    # latest 日志：需要复数拆分的类型做拆分，其余直接写入
    if event_type == "PHASE_PLAN_COMPLETED":
        entries = split_plural_field(
            log_entry, single="task_folder", plural="task_folders",
            accompaniments={"task_paths": "task_path"}
        )
    else:
        entries = [log_entry]

    # 持锁串行写入，避免并发 append 导致行交错
    with _LOG_LOCK:
        # 全量日志：原样写入（含复数 plan_paths 一条记录）
        append_jsonl(FULL_LOG_FILE, log_entry)
        for split_entry in entries:
            append_jsonl(LATEST_PROJECT_LOG_FILE, split_entry)

    return {"ok": True}


if __name__ == "__main__":
    # 启动时写 SERVER_STARTED 事件 + PID 文件，供 orchestrator 健康检查
    pid = os.getpid()
    pid_file = os.path.join(LOG_DIR, "report-event.pid")
    with open(pid_file, "w", encoding="utf-8") as f:
        f.write(str(pid))
    startup_entry = {
        "timestamp": now_iso_ms(),
        "agent_name": "report-event-server",
        "event_type": "SERVER_STARTED",
        "payload": {"pid": pid},
    }
    with _LOG_LOCK:
        append_jsonl(FULL_LOG_FILE, startup_entry)
        append_jsonl(LATEST_PROJECT_LOG_FILE, startup_entry)
    print(f"[report-event] SERVER_STARTED pid={pid}", file=sys.stderr)
    mcp.run()
