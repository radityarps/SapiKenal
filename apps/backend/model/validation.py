"""Validation helpers for server-side Keras model artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, NoReturn

import numpy as np

from config import settings

try:
    import tensorflow as tf  # pyright: ignore[reportMissingModuleSource]
except ImportError:  # Keep admin/auth routes testable without TensorFlow installed.
    tf = None


class ModelValidationError(ValueError):
    """A candidate model cannot be loaded or validated."""


class ModelContractError(ModelValidationError):
    """A loaded model does not satisfy the server inference contract."""


class ModelValidationUnavailable(RuntimeError):
    """The runtime cannot validate a model because TensorFlow is unavailable."""


CHUNK_SIZE = 1024 * 1024


def expected_classes() -> list[str]:
    """Return the class order used by the running inference pipeline."""
    return list(settings.labels)


def sha256_file(path: Path) -> str:
    """Hash a file incrementally without loading the artifact into memory."""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ModelValidationError("Model artifact cannot be read") from exc
    return digest.hexdigest()


def _shape_tuple(shape: Any) -> tuple[Any, ...] | None:
    """Normalize TensorFlow/Keras shape objects for contract comparison."""
    if shape is None:
        return None
    if isinstance(shape, (list, tuple)):
        if shape and isinstance(shape[0], (list, tuple)):
            return None
        return tuple(shape)
    try:
        return tuple(shape.as_list())
    except (AttributeError, TypeError, ValueError):
        return None


def _input_dtype_name(model: Any) -> str | None:
    """Return the first input dtype when the model exposes it."""
    inputs = getattr(model, "inputs", None)
    if inputs:
        try:
            dtype = getattr(inputs[0], "dtype", None)
        except (IndexError, TypeError):
            dtype = None
        if dtype is not None:
            return str(dtype).removeprefix("tf.").casefold()

    dtype = getattr(model, "input_dtype", None)
    if isinstance(dtype, str):
        return dtype.removeprefix("tf.").casefold()
    return None


def _raise_contract(message: str) -> NoReturn:
    raise ModelContractError(message)


def validate_loaded_model(
    model: Any,
    *,
    input_size: int,
    classes: list[str],
) -> dict[str, Any]:
    """Validate input/output shapes and warm a loaded candidate model."""
    if input_size != settings.input_size:
        _raise_contract(
            f"Model input size must be {settings.input_size} for the active pipeline"
        )

    expected = expected_classes()
    if classes != expected:
        _raise_contract(
            "Model classes must match the configured order: " + ", ".join(expected)
        )

    input_shape = _shape_tuple(getattr(model, "input_shape", None))
    expected_input_shape = (None, input_size, input_size, 3)
    if input_shape != expected_input_shape:
        _raise_contract(
            f"Model input shape must be {expected_input_shape}; received {input_shape}"
        )
    if input_shape is None:
        _raise_contract("Model input shape is unavailable")

    input_dtype = _input_dtype_name(model)
    if input_dtype is not None and input_dtype != "float32":
        _raise_contract(f"Model input type must be float32; received {input_dtype}")

    output_shape = _shape_tuple(getattr(model, "output_shape", None))
    expected_output_shape = (None, len(classes))
    if output_shape != expected_output_shape:
        _raise_contract(
            "Model output shape must be "
            f"{expected_output_shape}; received {output_shape}"
        )
    if output_shape is None:
        _raise_contract("Model output shape is unavailable")

    try:
        sample = np.zeros(
            (1, input_size, input_size, 3),
            dtype=np.float32,
        )
        output = model.predict(sample, verbose=0)
    except Exception as exc:
        raise ModelValidationError("Model warm-up failed") from exc

    values = np.asarray(output)
    expected_warmup_shape = (1, len(classes))
    if values.shape != expected_warmup_shape:
        _raise_contract(
            "Model warm-up output shape must be "
            f"{expected_warmup_shape}; received {values.shape}"
        )
    if not np.all(np.isfinite(values)):
        _raise_contract("Model warm-up produced non-finite output")
    if np.any(values < 0) or np.any(values > 1):
        _raise_contract("Model warm-up output must contain probabilities")
    if not np.allclose(values.sum(axis=1), 1.0, atol=1e-3, rtol=1e-3):
        _raise_contract("Model warm-up probabilities must sum to one")

    return {
        "input_shape": list(input_shape),
        "output_shape": list(output_shape),
        "classes": expected,
    }


def load_keras_model(path: Path) -> Any:
    """Load a Keras artifact using safe deserialization settings."""
    if tf is None:
        raise ModelValidationUnavailable("TensorFlow is not installed")
    try:
        return tf.keras.models.load_model(
            str(path),
            compile=False,
            safe_mode=True,
        )
    except TypeError as exc:
        # A runtime without safe_mode support cannot safely accept an upload.
        raise ModelValidationUnavailable(
            "The installed Keras runtime does not support safe model loading"
        ) from exc
    except Exception as exc:
        raise ModelValidationError("Model artifact cannot be deserialized") from exc


def validate_model_file(
    path: Path,
    *,
    input_size: int,
    classes: list[str],
) -> dict[str, Any]:
    """Validate a `.keras` file, including safe loading and warm-up."""
    if path.is_symlink() or not path.is_file():
        raise ModelValidationError("Model artifact is unavailable")
    if path.suffix.casefold() != ".keras":
        raise ModelValidationError("Only .keras model artifacts are accepted")
    try:
        if path.stat().st_size <= 0:
            raise ModelValidationError("Model artifact is empty")
    except OSError as exc:
        raise ModelValidationError("Model artifact cannot be inspected") from exc

    model = load_keras_model(path)
    metadata = validate_loaded_model(
        model,
        input_size=input_size,
        classes=classes,
    )
    metadata["checksum"] = sha256_file(path)
    return metadata
