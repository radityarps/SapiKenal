"""Main FastAPI application."""

from __future__ import annotations

import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
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
from sqlalchemy import desc, select  # pyright: ignore[reportMissingImports]
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
from db.core import SessionLocal, engine
from db.models import ModelActivation, ModelVersion
from inference_server import mark_model_unavailable, reload_active_model
from model.registry import (  # pyright: ignore[reportMissingImports]
    artifact_name_for,
    registry_root,
    resolve_artifact_path,
)
from model.validation import (  # pyright: ignore[reportMissingImports]
    sha256_file,
    validate_model_file,
)
from services.audit import record_audit
from utils.logger import get_logger

logger = get_logger(__name__)


def _register_startup_fallback(db) -> ModelVersion:
    """Copy an enabled fallback into the registry and record it as active."""
    source = Path(settings.model_path).expanduser().resolve()
    if (
        not source.is_file()
        or source.is_symlink()
        or source.suffix.casefold() != ".keras"
    ):
        raise ValueError("Configured fallback model artifact is unavailable")

    metadata = validate_model_file(
        source,
        input_size=settings.input_size,
        classes=list(settings.labels),
    )
    checksum = metadata["checksum"]
    artifact_name = artifact_name_for(settings.model_version, checksum)
    root = registry_root(create=True)
    destination = resolve_artifact_path(artifact_name)
    created_artifact = False
    if not destination.exists():
        with tempfile.NamedTemporaryFile(dir=root, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            try:
                with source.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        temporary.write(chunk)
                temporary.flush()
                os.fsync(temporary.fileno())
                os.replace(temporary_path, destination)
                created_artifact = True
            finally:
                temporary_path.unlink(missing_ok=True)
    if sha256_file(destination) != checksum:
        raise ValueError("Fallback model copy checksum does not match")
    reload_active_model(
        destination,
        settings.model_version,
        list(settings.labels),
        settings.input_size,
    )

    existing = db.scalar(
        select(ModelVersion).where(ModelVersion.version == settings.model_version)
    )
    if existing is not None:
        if (
            existing.checksum.casefold() != checksum.casefold()
            or existing.input_size != settings.input_size
            or existing.classes != list(settings.labels)
        ):
            raise ValueError("Fallback model version conflicts with registry metadata")
        existing.artifact_name = artifact_name
        existing.status = "active"
        existing.activated_at = datetime.now(timezone.utc)
        model = existing
    else:
        model = ModelVersion(
            version=settings.model_version,
            artifact_name=artifact_name,
            checksum=checksum,
            status="active",
            input_size=settings.input_size,
            classes=list(settings.labels),
            notes="Registered from the explicitly enabled startup fallback.",
            activated_at=datetime.now(timezone.utc),
        )
        db.add(model)
    db.flush()
    db.add(
        ModelActivation(
            model_version_id=model.id,
            previous_model_version_id=None,
            action="activate",
            reason="Explicit startup fallback registration",
            status="success",
        )
    )
    record_audit(
        db,
        action="model_fallback_registered",
        resource_type="model_version",
        resource_id=model.id,
        changed_fields={"status": "active", "source": "startup_fallback"},
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        if created_artifact:
            destination.unlink(missing_ok=True)
        raise
    return model


def _restore_active_model_from_registry() -> None:
    """Restore the database-selected model before serving inference traffic."""
    try:
        with SessionLocal() as db:
            active_models = db.scalars(
                select(ModelVersion)
                .where(ModelVersion.status == "active")
                .order_by(desc(ModelVersion.activated_at))
            ).all()
            if not active_models and settings.model_startup_fallback_enabled:
                _register_startup_fallback(db)
                logger.info(
                    "Registered startup fallback model version %s",
                    settings.model_version,
                )
                return
    except Exception as exc:
        mark_model_unavailable("Active model registry is unavailable")
        logger.error("Could not query the active model registry: %s", str(exc))
        raise

    if len(active_models) > 1:
        mark_model_unavailable("Multiple active model versions were found")
        logger.error("Model registry contains %d active versions", len(active_models))
        raise RuntimeError("Model registry contains multiple active versions")

    active = active_models[0] if active_models else None
    if active is None:
        mark_model_unavailable("No active model has been registered")
        return

    try:
        artifact_path = resolve_artifact_path(active.artifact_name)
        if not artifact_path.is_file() or artifact_path.suffix.casefold() != ".keras":
            raise ValueError("Active model artifact is unavailable")
        if sha256_file(artifact_path).casefold() != active.checksum.casefold():
            raise ValueError("Active model checksum does not match the registry")
        reload_active_model(
            artifact_path,
            active.version,
            active.classes,
            active.input_size,
        )
        logger.info("Restored active model version %s", active.version)
    except Exception as exc:
        mark_model_unavailable("Active model recovery failed")
        logger.error(
            "Could not restore active model version %s: %s",
            active.version,
            str(exc),
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create development tables and restore the selected model before serving."""
    if settings.fastapi_env == "development" and settings.debug:
        await asyncio.to_thread(Base.metadata.create_all, bind=engine)
        logger.info("Development database tables ensured")
    try:
        await asyncio.to_thread(_restore_active_model_from_registry)
    except Exception as exc:
        logger.error("Active model recovery could not query the registry: %s", str(exc))
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
