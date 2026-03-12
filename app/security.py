import os
import threading
import time

API_KEY = os.getenv("VISIONFLOW_API_KEY", "")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 60))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))

_LIMIT_STATE = {}
_LOCK = threading.Lock()


def auth_required() -> bool:
    return bool(API_KEY)


def verify_api_key(provided: str | None) -> bool:
    if not auth_required():
        return True
    return provided == API_KEY


def _bucket_key(client_id: str):
    window_start = int(time.time() // RATE_LIMIT_WINDOW_SECONDS) * RATE_LIMIT_WINDOW_SECONDS
    return f"{client_id}:{window_start}"


def allow_request(client_id: str) -> bool:
    now = time.time()
    with _LOCK:
        expired = [key for key, value in _LIMIT_STATE.items() if (now - value["window_start"]) > RATE_LIMIT_WINDOW_SECONDS]
        for key in expired:
            del _LIMIT_STATE[key]

        key = _bucket_key(client_id)
        state = _LIMIT_STATE.get(key)
        if state is None:
            _LIMIT_STATE[key] = {"count": 1, "window_start": int(now)}
            return True
        if state["count"] >= RATE_LIMIT_REQUESTS:
            return False
        state["count"] += 1
        return True
