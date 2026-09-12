"""Main FastAPI application."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from fastapi import (  # pyright: ignore[reportMissingImports]
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.middleware.cors import (  # pyright: ignore[reportMissingImports]
    CORSMiddleware,
)
from starlette.responses import JSONResponse  # pyright: ignore[reportMissingImports]

import db.models  # noqa: F401 - register every model with Base.metadata
from api.admin_routes import content_router
from api.admin_routes import router as admin_router
from api.auth_routes import router as auth_router
from api.benchmark_guard import BenchmarkEndpointGuardMiddleware
from api.rate_limiter import RateLimiterMiddleware
from api.routes import router
from config import settings
from db.base import Base
from db.core import engine
from inference_server import mark_model_unavailable, reload_active_model
from utils.logger import get_logger

logger = get_logger(__name__)


def _load_static_model() -> None:
    """Load the configured static model artifact before serving inference traffic."""
    source = Path(settings.model_path).expanduser().resolve()
    if (
        not source.is_file()
        or source.is_symlink()
        or source.suffix.casefold() != ".keras"
    ):
        mark_model_unavailable("Configured model artifact is unavailable")
        logger.error(
            "Model file %s does not exist or is not a valid .keras file", source
        )
        return

    try:
        reload_active_model(
            source,
            settings.model_version,
            list(settings.labels),
            settings.input_size,
        )
        logger.info("Loaded model from %s (version: %s)", source, settings.model_version)
    except Exception as exc:
        mark_model_unavailable("Model loading failed")
        logger.error("Could not load model from %s: %s", source, str(exc))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create development tables and load the configured model before serving."""
    if settings.fastapi_env == "development" and settings.debug:
        await asyncio.to_thread(Base.metadata.create_all, bind=engine)
        logger.info("Development database tables ensured")
    try:
        await asyncio.to_thread(_load_static_model)
    except Exception as exc:
        logger.error("Model loading error: %s", str(exc))
    yield


# Create FastAPI app
app = FastAPI(
    title="SapiKenal Backend",
    description="Cattle breed identification API for four supported classes.",
    version=settings.model_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Hide benchmark-only routes before multipart parsing unless explicitly enabled.
app.add_middleware(BenchmarkEndpointGuardMiddleware)

# CORS middleware - Android does not require browser CORS; web is allowlisted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.web_origin.split(",") if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Rate limiter middleware - per-IP sliding window for /api/predict
app.add_middleware(
    RateLimiterMiddleware,
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

# Include routes
app.include_router(router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(content_router)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach a correlation ID for admin/audit requests without trusting client data."""
    import uuid

    request.state.request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers.setdefault("x-request-id", request.state.request_id)
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SapiKenal Backend",
        "version": settings.model_version,
        "docs": "/docs",
        "status": "running",
    }


def _resolve_error_code(exc: HTTPException) -> str:
    """Map HTTPException status code to a defined error code."""
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        detail = cast(dict[str, Any], exc.detail)
        return str(detail["error_code"])
    if exc.status_code == 422:
        return "INVALID_IMAGE"
    elif exc.status_code == 503:
        return "MODEL_NOT_READY"
    elif exc.status_code == 408:
        return "TIMEOUT"
    elif exc.status_code == 429:
        return "RATE_LIMITED"
    else:
        return "INFERENCE_FAILED"


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Convert HTTP errors to the mobile or admin error contract."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        content = {
            "status": "error",
            "code": exc.detail["code"],
            "message": str(exc.detail.get("message", "Request failed"))[:256],
            "request_id": getattr(request.state, "request_id", "unknown"),
            "field_errors": exc.detail.get("field_errors", {}),
        }
    elif isinstance(exc.detail, dict) and "error_code" in exc.detail:
        detail = cast(dict[str, Any], exc.detail)
        content = {
            "status": "error",
            "error_code": str(detail["error_code"]),
            "message": str(detail.get("message", "Request failed"))[:256],
        }
        for key in (
            "model_info",
            "processing_time_ms",
            "preprocessing_time_ms",
            "inference_time_ms",
        ):
            if key in detail:
                content[key] = detail[key]
    else:
        content = {
            "status": "error",
            "error_code": _resolve_error_code(exc),
            "message": str(exc.detail)[:256],
        }
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc!s}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INFERENCE_FAILED",
            "message": "Internal server error",
        },
    )


if __name__ == "__main__":
    import importlib

    uvicorn = importlib.import_module("uvicorn")
    logger.info(f"Starting SapiKenal Backend (v{settings.model_version})")
    logger.info(f"Environment: {settings.fastapi_env}")
    logger.info(f"Device: {settings.device}")
    logger.info(f"Model path: {settings.model_path}")

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )
