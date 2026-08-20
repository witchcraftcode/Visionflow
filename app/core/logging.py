import json
import logging
from contextvars import ContextVar
from typing import Any


request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("visionflow")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


LOGGER = configure_logging()


def set_request_id(request_id: str | None):
    request_id_context.set(request_id)


def log_event(event: str, **fields: Any):
    request_id = request_id_context.get()
    payload = {"event": event, **fields}
    if request_id and "request_id" not in payload and "trace_id" not in payload:
        payload["request_id"] = request_id
    LOGGER.info(json.dumps(payload, sort_keys=True))
