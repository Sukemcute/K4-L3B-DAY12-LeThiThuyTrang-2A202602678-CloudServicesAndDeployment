"""CP1 — Structured logging.

`print("user abc hỏi gì đó")` là log cho người đọc. Cloud (Railway, Render,
Cloud Run, Datadog...) đọc log bằng máy: một dòng = một JSON object thì mới
lọc/đếm/cảnh báo được. Đây là khác biệt lớn giữa localhost và production.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """CHO SẴN — thời điểm hiện tại theo ISO-8601, múi giờ UTC."""
    return datetime.now(timezone.utc).isoformat()


def log_event(event: str, level: str = "info", **fields) -> str:
    """Ghi một dòng log JSON chi tiết ra stdout.

    Bao gồm các trường chuẩn hóa:
        - "event"     : tên sự kiện
        - "level"     : mức log (viết thường: info, warn, error...)
        - "timestamp" : thời điểm ISO-8601 UTC
        - "service"   : tên dịch vụ (mặc định day12-agent nếu chưa có)
        - "pid"       : process ID phục vụ quan sát đa tiến trình/container
        - "message"   : tóm tắt nội dung dễ đọc cho con người
        - **fields    : các trường metadata chi tiết (user_id, cost_usd, tokens...)
    """
    clean_level = level.lower()
    
    # Sinh message tóm tắt trực quan nếu chưa được truyền vào
    message = fields.pop("message", None)
    if not message:
        if event == "ask_completed":
            uid = fields.get("user_id", "anonymous")
            cost = fields.get("cost_usd", 0.0)
            message = f"AI agent responded for user='{uid}' (cost=${cost:.6f})"
        elif event == "service_started":
            message = f"Service started successfully (version={fields.get('version', 'unknown')})"
        elif event == "service_stopped":
            message = "Service stopped gracefully"
        else:
            message = f"Event '{event}' recorded"

    service_name = fields.pop("service", "day12-agent")

    payload = {
        "timestamp": utc_now_iso(),
        "level": clean_level,
        "service": service_name,
        "pid": os.getpid(),
        "event": event,
        "message": message,
        **fields,
    }

    line = json.dumps(payload, ensure_ascii=False, default=str)
    print(line)
    return line
