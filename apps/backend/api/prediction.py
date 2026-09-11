"""Shared image-prediction workflow for REST and WebSocket transports."""

import asyncio
import io
import time
from typing import Any, cast

from fastapi import HTTPException  # pyright: ignore[reportMissingImports]
from PIL import Image, ImageOps

from config import settings
from inference_server import get_inference_service, is_model_ready
from utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})


def error_payload_for_http_exception(exc: HTTPException) -> dict[str, Any]:
    """Build the error envelope shared by HTTP and WebSocket responses."""
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        detail = cast(dict[str, Any], exc.detail)
        payload: dict[str, Any] = {
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
                payload[key] = detail[key]
        return payload

    error_code = {
        408: "TIMEOUT",
        422: "INVALID_IMAGE",
        429: "RATE_LIMITED",
        503: "MODEL_NOT_READY",
    }.get(exc.status_code, "INFERENCE_FAILED")
    return {
        "status": "error",
        "error_code": error_code,
        "message": str(exc.detail)[:256],
    }


async def predict_image_bytes(
    image_bytes: bytes,
    content_type: str | None,
) -> tuple[dict[str, Any], float]:
    """Validate, decode, and classify image bytes using the shared CNN workflow.

    The returned duration covers validation, image decoding, preprocessing,
    inference, and response construction. It is measured with ``perf_counter``
    so the transport benchmark can distinguish backend work from end-to-end time.
    """
    started_at = time.perf_counter()

    if not is_model_ready():
        raise HTTPException(status_code=503, detail="Model not loaded")

    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid image format. Accepted: JPEG, PNG, WebP. Got: {content_type}"
            ),
        )

    if not image_bytes:
        raise HTTPException(status_code=422, detail="Empty image file")

    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert(
            "RGB"
        )
    except Exception as exc:
        logger.warning("Failed to open image: %s", exc)
        raise HTTPException(
            status_code=422, detail="Invalid or corrupted image file"
        ) from exc

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(get_inference_service().predict, image),
            timeout=settings.request_timeout,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=408,
            detail="Request processing exceeded timeout",
        ) from exc

    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Inference failed"),
        )

    server_processing_ms = round((time.perf_counter() - started_at) * 1_000, 3)
    return result, server_processing_ms
