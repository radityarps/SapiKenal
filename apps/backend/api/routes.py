"""FastAPI routes used by the mobile app."""

from __future__ import annotations

import asyncio

from config import settings
from db.core import get_db
from db.models import ModelVersion
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from inference_server import get_model_status
from services.audit import record_prediction_event, sync_history_to_admin
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from utils.logger import get_logger

from api.history_store import history_store
from api.prediction import error_payload_for_http_exception, predict_image_bytes
from api.schemas import (
    HealthResponse,
    HistoryCreate,
    HistoryListResponse,
    HistoryRecord,
    HistoryUpsertResponse,
    PredictResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["mobile"])


def _record_prediction_error(request_id: str, error_payload: dict) -> None:
    """Record an HTTP prediction failure without retaining image bytes."""
    error_code = error_payload["error_code"]
    rejection = error_payload.get("rejection") or {}
    is_rejection = error_code == "NON_CATTLE_IMAGE"
    record_prediction_event(
        request_id=request_id,
        status="rejected" if is_rejection else "failed",
        outcome="rejected" if is_rejection else "failed",
        error_code=error_code,
        predicted_class="non_cattle" if is_rejection else None,
        confidence=rejection.get("confidence"),
        scores=rejection.get("scores"),
        processing_ms=error_payload.get("processing_time_ms"),
        model_version=(error_payload.get("model_info") or {}).get("version"),
    )


@router.post("/predict", response_model=PredictResponse)
async def predict(request: Request, image: UploadFile = File(...)):
    """
    Predict cattle disease from image.

    NO-RETENTION: uploaded image bytes stay in memory only; backend does not write
    images to disk. Mobile stores local history image path.
    """
    try:
        result, processing_ms = await predict_image_bytes(
            await image.read(), image.content_type
        )
    except HTTPException as exc:
        _record_prediction_error(
            getattr(request.state, "request_id", "unknown"),
            error_payload_for_http_exception(exc),
        )
        raise
    prediction = result.get("prediction") or {}
    record_prediction_event(
        request_id=getattr(request.state, "request_id", "unknown"),
        status="success",
        outcome=prediction.get("outcome", "accepted"),
        predicted_class=prediction.get("disease_class"),
        confidence=prediction.get("confidence"),
        scores=prediction.get("scores"),
        processing_ms=processing_ms,
        model_version=(result.get("model_info") or {}).get("version"),
    )
    return result


@router.post("/benchmark/predict")
async def benchmark_predict(image: UploadFile = File(...)):
    """Run the REST transport benchmark without altering the production endpoint.

    This route intentionally omits the production rate limit. It only becomes
    available when ``BENCHMARK_ENABLED=true`` is configured in the server
    environment and is not part of the Android API contract.
    """
    if not settings.benchmark_enabled:
        raise HTTPException(status_code=404, detail="Benchmark endpoints are disabled")

    result, server_processing_ms = await predict_image_bytes(
        await image.read(), image.content_type
    )
    return {**result, "benchmark": {"server_processing_ms": server_processing_ms}}


@router.post("/benchmark/echo")
async def benchmark_echo(payload: UploadFile = File(...)):
    """Echo a multipart payload to isolate REST transport overhead."""
    if not settings.benchmark_enabled:
        raise HTTPException(status_code=404, detail="Benchmark endpoints are disabled")

    started_at = asyncio.get_running_loop().time()
    payload_size_bytes = len(await payload.read())
    server_processing_ms = round(
        (asyncio.get_running_loop().time() - started_at) * 1_000,
        3,
    )
    return {
        "status": "success",
        "payload_size_bytes": payload_size_bytes,
        "benchmark": {"server_processing_ms": server_processing_ms},
    }


async def _benchmark_websocket_exchange(websocket: WebSocket) -> None:
    """Process benchmark messages on one persistent WebSocket connection.

    Each exchange requires a JSON metadata frame followed by a binary payload
    frame. ``operation`` is either ``predict`` or ``echo``. The response shape
    matches its REST benchmark counterpart, including benchmark timing metadata.
    """
    await websocket.accept()

    while True:
        try:
            metadata = await websocket.receive_json()
            if not isinstance(metadata, dict):
                await websocket.send_json(
                    {
                        "status": "error",
                        "error_code": "INVALID_REQUEST",
                        "message": "Metadata must be a JSON object",
                    }
                )
                continue

            operation = metadata.get("operation")
            if operation not in {"predict", "echo"}:
                await websocket.send_json(
                    {
                        "status": "error",
                        "error_code": "INVALID_REQUEST",
                        "message": "Unsupported benchmark operation",
                    }
                )
                continue

            payload = await websocket.receive_bytes()
            if operation == "echo":
                started_at = asyncio.get_running_loop().time()
                result = {
                    "status": "success",
                    "payload_size_bytes": len(payload),
                    "benchmark": {
                        "server_processing_ms": round(
                            (asyncio.get_running_loop().time() - started_at) * 1_000,
                            3,
                        )
                    },
                }
            else:
                try:
                    prediction, server_processing_ms = await predict_image_bytes(
                        payload,
                        metadata.get("content_type"),
                    )
                    result = {
                        **prediction,
                        "benchmark": {"server_processing_ms": server_processing_ms},
                    }
                except HTTPException as exc:
                    result = error_payload_for_http_exception(exc)

            await websocket.send_json(result)
        except WebSocketDisconnect:
            return
        except Exception as exc:
            logger.error("Benchmark WebSocket exchange failed: %s", exc, exc_info=True)
            await websocket.send_json(
                {
                    "status": "error",
                    "error_code": "INFERENCE_FAILED",
                    "message": "Internal benchmark server error",
                }
            )


@router.websocket("/benchmark/ws")
async def benchmark_websocket(websocket: WebSocket):
    """Benchmark-only persistent WebSocket transport endpoint."""
    if not settings.benchmark_enabled:
        await websocket.close(code=1008, reason="Benchmark endpoints are disabled")
        return

    await _benchmark_websocket_exchange(websocket)


@router.get("/health", response_model=HealthResponse)
async def health(db: Session = Depends(get_db)):
    try:
        model_status = get_model_status()
        active_models = db.scalars(
            select(ModelVersion)
            .where(ModelVersion.status == "active")
            .order_by(desc(ModelVersion.activated_at))
        ).all()
        actual_version = model_status.get("model_version", settings.model_version)
        registry_consistent = (
            len(active_models) == 1 and actual_version == active_models[0].version
        )
        return {
            "status": (
                "ok"
                if model_status["model_loaded"] and registry_consistent
                else "degraded"
            ),
            "model_loaded": model_status["model_loaded"],
            "model_version": actual_version,
        }
    except Exception as exc:
        logger.error("Health check failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "model_loaded": False,
                "model_version": "unknown",
            },
        )


@router.post("/history", response_model=HistoryUpsertResponse)
async def upsert_history(item: HistoryCreate):
    item_data = item.model_dump(mode="json")
    row = await asyncio.to_thread(history_store.upsert, item_data)
    await asyncio.to_thread(sync_history_to_admin, item_data)
    return {"status": "success", "item": HistoryRecord.from_row(row)}


@router.get("/history", response_model=HistoryListResponse)
async def list_history(
    device_id: str = Query(min_length=8, max_length=128),
    limit: int = Query(default=100, ge=1, le=500),
):
    rows = await asyncio.to_thread(history_store.list, device_id, limit)
    return {"status": "success", "items": [HistoryRecord.from_row(row) for row in rows]}


@router.delete("/history/{history_id}")
async def delete_history(
    history_id: int, device_id: str = Query(min_length=8, max_length=128)
):
    deleted = await asyncio.to_thread(history_store.delete, history_id, device_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History item not found")
    return {"status": "success"}
