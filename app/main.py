from fastapi import FastAPI

from app import security
from app.api.v1.router import api_router
from app.audit import list_admin_audit_events, record_admin_audit_event
from app.core.config import settings
from app.core.middleware import add_exception_handlers, add_middleware, trace_id_from_request
from app.services import queue, registry

import os

def create_app() -> FastAPI:
    is_production = os.getenv("ENV") == "production"

    app = FastAPI(
        title=settings.app_name,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    @app.get("/", include_in_schema=False)
    def home():
        return {
            "project": "VisionFlow",
            "status": "live",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics"
        }

    add_exception_handlers(app)
    add_middleware(app)

    app.include_router(api_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()

# Backward-compatible imports for scripts/tests that historically patched app.main.
allow_request = security.allow_request
verify_admin_key = security.verify_admin_key
verify_api_key = security.verify_api_key

dead_letter_depth = queue.dead_letter_depth
enqueue_job = queue.enqueue_job
get_idempotency_job = queue.get_idempotency_job
get_job = queue.get_job
ping = queue.ping
queue_depth = queue.queue_depth
set_idempotency_job = queue.set_idempotency_job
set_job = queue.set_job

has_model = registry.has_model
list_model_versions = registry.list_model_versions
list_models = registry.list_models
model_metadata = registry.model_metadata
promote_model_version = registry.promote_model_version
register_model_version = registry.register_model_version
resolve_model_version = registry.resolve_model_version

