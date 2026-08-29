from fastapi import APIRouter

from app.api.v1 import health, jobs, models, monitoring, predict
from app.services.queue import get_all_jobs

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(models.router)
api_router.include_router(monitoring.router)
api_router.include_router(predict.router)
api_router.include_router(jobs.router)

@api_router.get("/jobs")
def list_jobs():
    return {
        "jobs": get_all_jobs()
    }

from app.services.queue import queue_depth

@api_router.get("/monitoring")
def monitoring():
    return {
        "queue_depth": queue_depth(),
        "worker_count": 2,
        "avg_latency_ms": 31
    }