import os

from app.queue.redis_queue import consume_rate_limit

API_KEY = os.getenv("VISIONFLOW_API_KEY", "")
ADMIN_API_KEY = os.getenv("VISIONFLOW_ADMIN_API_KEY", "")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 60))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))


def auth_required() -> bool:
    return bool(API_KEY)


def verify_api_key(provided: str | None) -> bool:
    if not auth_required():
        return True
    return provided == API_KEY


def admin_auth_required() -> bool:
    return bool(ADMIN_API_KEY or API_KEY)


def verify_admin_key(provided: str | None) -> bool:
    expected = ADMIN_API_KEY or API_KEY
    if not expected:
        return True
    return provided == expected


def allow_request(client_id: str) -> bool:
    return consume_rate_limit(client_id, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
