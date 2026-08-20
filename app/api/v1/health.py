from fastapi import APIRouter, Response

from app.observability import metrics_payload, set_dead_letter_depth, set_queue_depth
from app.services import queue

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    try:
        redis_ok = queue.ping()
        q_depth = queue.queue_depth()
        dlq_depth = queue.dead_letter_depth()
    except Exception:
        redis_ok = False
        q_depth = 0
        dlq_depth = 0
    set_queue_depth(q_depth)
    set_dead_letter_depth(dlq_depth)
    return {
        "status": "ok" if redis_ok else "degraded",
        "dependencies": {"redis": "ok" if redis_ok else "down"},
        "queue_depth": q_depth,
        "dead_letter_depth": dlq_depth,
    }


@router.get("/metrics")
def metrics():
    body, content_type = metrics_payload()
    return Response(content=body, media_type=content_type)
