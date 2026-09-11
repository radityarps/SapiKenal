"""Model loading module with a process-local singleton model."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any

try:
    import tensorflow as tf  # pyright: ignore[reportMissingModuleSource]
except ImportError:  # Keep auth/admin routes testable in a lightweight environment.
    tf = None

from model.validation import (
    validate_loaded_model,  # pyright: ignore[reportMissingImports]
)
from utils.errors import ModelLoadError
from utils.logger import get_logger

logger = get_logger(__name__)
_MODEL_LOCK = RLock()


class ModelLoader:
    """Load one inference model and swap candidates only after validation."""

    _instance: ModelLoader | None = None
    _initialized: bool = False
    model: Any

    def __new__(cls, model_path: str = "./model/best.keras"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        if not cls._instance._initialized:
            cls._instance.model = cls._instance._load_model(model_path)
            cls._instance._initialized = True

        return cls._instance

    def _load_model(self, model_path: str) -> Any:
        """Load a model into an isolated object without changing the active one."""
        try:
            if tf is None:
                raise ModelLoadError("TensorFlow is not installed")
            path = Path(model_path)

            if not path.exists():
                raise ModelLoadError(f"Model file not found: {model_path}")

            logger.info("Loading model from %s", model_path)
            try:
                model = tf.keras.models.load_model(
                    model_path,
                    compile=False,
                    safe_mode=True,
                )
            except TypeError as exc:
                raise ModelLoadError(
                    "The installed Keras runtime does not support safe model loading"
                ) from exc
            logger.info(
                "Model loaded successfully. Parameters: %s", model.count_params()
            )
            return model
        except ModelLoadError:
            raise
        except Exception as exc:
            raise ModelLoadError(f"Failed to load model: {exc!s}") from exc

    def reload(
        self,
        model_path: str,
        *,
        input_size: int,
        classes: list[str],
    ) -> None:
        """Validate and atomically install a candidate model."""
        candidate = self._load_model(model_path)
        validate_loaded_model(
            candidate,
            input_size=input_size,
            classes=classes,
        )
        with _MODEL_LOCK:
            self.model = candidate

    def predict(self, image_array: Any) -> Any:
        """Run inference using a stable reference to the active model."""
        try:
            with _MODEL_LOCK:
                model = self.model
            return model.predict(image_array, verbose=0)
        except Exception as exc:
            raise ModelLoadError(f"Model inference failed: {exc!s}") from exc
