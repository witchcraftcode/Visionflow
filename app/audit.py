import json
import os
from datetime import datetime, timezone
from typing import Any

from app.queue.redis_queue import redis_client

AUDIT_STREAM_KEY = "audit:admin"
AUDIT_LOG_LIMIT = int(os.getenv("AUDIT_LOG_LIMIT", 200))


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_admin_audit_event(action: str, **fields: Any) -> dict[str, Any]:
    entry = {
        "timestamp": _now_utc_iso(),
        "action": action,
        **fields,
    }
    redis_client.lpush(AUDIT_STREAM_KEY, json.dumps(entry))
    redis_client.ltrim(AUDIT_STREAM_KEY, 0, max(AUDIT_LOG_LIMIT - 1, 0))
    return entry


def list_admin_audit_events(limit: int = 50) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(limit, AUDIT_LOG_LIMIT))
    raw_entries = redis_client.lrange(AUDIT_STREAM_KEY, 0, bounded_limit - 1)
    return [json.loads(entry) for entry in raw_entries]
