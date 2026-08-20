from fastapi import APIRouter

from app.api.v1 import health, jobs, models, monitoring, predict

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(models.router)
api_router.include_router(monitoring.router)
api_router.include_router(predict.router)
api_router.include_router(jobs.router)
