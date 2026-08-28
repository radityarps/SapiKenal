"""Core inference service - NO FastAPI/HTTP coupling."""

import time
from contextlib import nullcontext
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np
from config import settings
from model.loader import ModelLoader
from model.validation import validate_loaded_model
from PIL import Image
from preprocessing.model_preprocessor import ModelPreprocessor
from utils.errors import InferenceError
from utils.logger import get_logger

logger = get_logger(__name__)

DISPLAY_LABEL_KEY_MAP = {
    "FMD": "disease.fmd",
    "LSD": "disease.lsd",
    "healthy": "disease.healthy",
    "non_cattle": "validation.non_cattle",
}


class InferenceService:
    """
    Pure inference logic with NO HTTP/FastAPI coupling.
    Can be called from FastAPI, Go, or any other framework.

    Designed for easy migration to Go + Python microservice architecture.
    """

    # Labels from config: FMD, healthy, LSD, non_cattle.
    LABELS = settings.labels
    CONFIDENCE_THRESHOLD = settings.confidence_threshold  # 0.60

    def __init__(self, model_path: str | None = None):
        """Initialize inference service with singleton model loader."""
        self.model_loader = ModelLoader(model_path or settings.model_path)
        validate_loaded_model(
            self.model_loader.model,
            input_size=settings.input_size,
            classes=list(self.LABELS),
        )
        self.preprocessor = ModelPreprocessor()
        self._runtime_lock = RLock()
        self._model_version = settings.model_version
        logger.info("InferenceService initialized")

    @property
    def model_version(self) -> str:
        """Return the version paired with the currently installed model."""
        runtime_lock = getattr(self, "_runtime_lock", nullcontext())
        with runtime_lock:
            return getattr(self, "_model_version", settings.model_version)

    def reload_model(
        self,
        model_path: Path,
        version: str,
        classes: list[str],
        input_size: int = settings.input_size,
    ) -> None:
        """Validate, warm, and atomically install a candidate model."""
        if classes != list(self.LABELS):
            raise ValueError("Candidate classes do not match the active model contract")
        with self._runtime_lock:
            self.model_loader.reload(
                str(model_path),
                input_size=input_size,
                classes=classes,
            )
            self._model_version = version
            settings.model_path = str(model_path)
            settings.model_version = version

    def predict(self, image: Image.Image) -> dict[str, Any]:
        """
        Pure inference - NO HTTP logic.

        Args:
            image: PIL Image in RGB format

        Returns:
            Dict with prediction results
        """
        start_time = time.time()

        try:
            # Preprocessing: Convert image to numpy array
            image_array = self.preprocessor.process(image)

            preprocessing_ms = int((time.time() - start_time) * 1000)
            infer_start = time.time()

            # Snapshot the model and its version under one lock so the response
            # metadata always describes the model that produced these scores.
            runtime_lock = getattr(self, "_runtime_lock", nullcontext())
            with runtime_lock:
                runtime_version = getattr(
                    self, "_model_version", settings.model_version
                )
                # The deployed Keras model already returns softmax probabilities.
                probs = self.model_loader.predict(image_array)[0]

            inference_ms = int((time.time() - infer_start) * 1000)
            total_ms = int((time.time() - start_time) * 1000)

            # Get prediction
            pred_idx = int(np.argmax(probs))
            pred_label = self.LABELS[pred_idx]
            pred_confidence = float(probs[pred_idx])
            is_reliable = (
                pred_label != "non_cattle"
                and pred_confidence >= self.CONFIDENCE_THRESHOLD
            )
            outcome = "rejected" if pred_label == "non_cattle" else "accepted"

            # Log inference
            logger.info(
                f"Inference: {pred_label} ({pred_confidence:.2%}) "
                f"preprocessing={preprocessing_ms}ms, "
                f"inference={inference_ms}ms, "
                f"total={total_ms}ms"
            )

            # Build response
            result = {
                "status": "success",
                "prediction": {
                    "outcome": outcome,
                    "disease_class": pred_label,
                    "display_label_key": DISPLAY_LABEL_KEY_MAP[pred_label],
                    "confidence": round(pred_confidence, 4),
                    "is_reliable": is_reliable,
                    "scores": {
                        self.LABELS[i]: round(float(probs[i]), 4)
                        for i in range(len(self.LABELS))
                    },
                },
                "model_info": {"version": runtime_version},
                "processing_time_ms": total_ms,
                "preprocessing_time_ms": preprocessing_ms,
                "inference_time_ms": inference_ms,
            }

            return result

        except Exception as e:
            logger.error(f"Inference failed: {e!s}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }


_service_init_error: str | None = None

# Singleton instance. The configured model path is only a startup fallback when
# explicitly enabled; otherwise the database-selected active model is restored by
# the application lifespan before traffic is served.
if settings.model_startup_fallback_enabled:
    try:
        inference_service: InferenceService | None = InferenceService()
    except Exception as exc:
        inference_service = None
        _service_init_error = str(exc)
        logger.warning(
            "Inference service unavailable at startup. "
            "API will run in degraded mode until model is provided.",
            extra={"model_path": settings.model_path, "error": _service_init_error},
        )
else:
    inference_service = None
    _service_init_error = "No active model has been restored from the registry"


def reload_active_model(
    model_path: Path,
    version: str,
    classes: list[str],
    input_size: int = settings.input_size,
) -> None:
    """Warm and atomically swap the single-worker inference model."""
    global inference_service, _service_init_error
    if inference_service is None:
        candidate_service = InferenceService(str(model_path))
        candidate_service.reload_model(model_path, version, classes, input_size)
        inference_service = candidate_service
    else:
        inference_service.reload_model(model_path, version, classes, input_size)
    _service_init_error = None


def mark_model_unavailable(message: str) -> None:
    """Disable inference after an active model cannot be restored."""
    global inference_service, _service_init_error
    inference_service = None
    _service_init_error = message


def is_model_ready() -> bool:
    """Return True when inference model is loaded and ready."""
    return inference_service is not None


def get_inference_service() -> InferenceService:
    """Return active inference service or raise a clear error when unavailable."""
    if inference_service is None:
        error_message = _service_init_error or "Model service not initialized"
        raise InferenceError(
            f"Model not loaded. Expected file at '{settings.model_path}'. "
            f"Startup error: {error_message}"
        )
    return inference_service


def get_model_status() -> dict[str, Any]:
    """Expose model readiness details for health endpoint."""
    return {
        "model_loaded": inference_service is not None,
        "model_path": settings.model_path,
        "model_version": (
            inference_service.model_version
            if inference_service is not None
            else settings.model_version
        ),
        "error": _service_init_error,
    }
