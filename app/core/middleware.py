import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app import security
from app.core.config import settings
from app.core.logging import log_event, set_request_id
from app.observability import track_http_metrics


def api_path(path: str) -> str:
    if path.startswith(f"{settings.api_v1_prefix}/"):
        return path.removeprefix(settings.api_v1_prefix)
    return path


def trace_id_from_request(request: Request):
    return getattr(request.state, "trace_id", "unknown")


def error_payload(code: str, message: str, details: dict[str, Any], trace_id: str):
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "trace_id": trace_id,
        }
    }


def is_admin_path(path: str, method: str = "GET") -> bool:
    normalized = api_path(path)
    if normalized.startswith("/models/") and method in {"POST", "PUT", "PATCH", "DELETE"}:
        return True
    return normalized in settings.admin_paths or (
        normalized.startswith("/models/") and normalized.endswith("/promote")
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        trace_id = request.headers.get("X-Request-ID") or request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        request.state.trace_id = trace_id
        request.state.request_id = trace_id
        set_request_id(trace_id)

        normalized_path = api_path(request.url.path)
        if normalized_path not in settings.exempt_paths:
            api_key = request.headers.get("X-API-Key")
            if not security.verify_api_key(api_key):
                response = JSONResponse(
                    status_code=401,
                    content=error_payload(
                        code="unauthorized",
                        message="Missing or invalid API key",
                        details={"header": "X-API-Key"},
                        trace_id=trace_id,
                    ),
                )
                response.headers["X-Trace-Id"] = trace_id
                response.headers["X-Request-ID"] = trace_id
                track_http_metrics(request.method, request.url.path, 401, start_time)
                return response

            client_id = api_key or (request.client.host if request.client else "unknown")
            if not security.allow_request(client_id):
                response = JSONResponse(
                    status_code=429,
                    content=error_payload(
                        code="rate_limited",
                        message="Rate limit exceeded",
                        details={},
                        trace_id=trace_id,
                    ),
                )
                response.headers["X-Trace-Id"] = trace_id
                response.headers["X-Request-ID"] = trace_id
                track_http_metrics(request.method, request.url.path, 429, start_time)
                return response

            if is_admin_path(request.url.path, request.method):
                admin_key = request.headers.get("X-Admin-Key")
                if not security.verify_admin_key(admin_key):
                    response = JSONResponse(
                        status_code=403,
                        content=error_payload(
                            code="forbidden",
                            message="Missing or invalid admin API key",
                            details={"header": "X-Admin-Key"},
                            trace_id=trace_id,
                        ),
                    )
                    response.headers["X-Trace-Id"] = trace_id
                    response.headers["X-Request-ID"] = trace_id
                    track_http_metrics(request.method, request.url.path, 403, start_time)
                    return response

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Request-ID"] = trace_id
        track_http_metrics(request.method, request.url.path, response.status_code, start_time)
        log_event("http_request", method=request.method, path=request.url.path, status_code=response.status_code)
        return response


def add_middleware(app: FastAPI):
    app.add_middleware(RequestContextMiddleware)


def add_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        details = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code="http_error",
                message="Request failed",
                details=details,
                trace_id=trace_id_from_request(request),
            ),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_payload(
                code="internal_error",
                message="Unexpected server error",
                details={"exception": str(exc)},
                trace_id=trace_id_from_request(request),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_payload(
                code="validation_error",
                message="Validation failed",
                details={"errors": exc.errors()},
                trace_id=trace_id_from_request(request),
            ),
        )
