from __future__ import annotations

from types import SimpleNamespace

import numpy as np  # pyright: ignore[reportMissingImports]
import pytest

from config import settings
from model.validation import (
    ModelContractError,
    validate_loaded_model,
)


class Rescaling:
    def get_config(self):
        return {"scale": 1 / 127.5, "offset": -1.0}


class Dense:
    def get_config(self):
        return {"units": 4, "activation": "softmax"}


class FakeModel:
    input_shape = (None, 224, 224, 3)
    output_shape = (None, 4)
    inputs = [SimpleNamespace(dtype="float32")]
    outputs = [SimpleNamespace(dtype="float32")]

    def __init__(self, output: np.ndarray) -> None:
        self.output = output
        self.layers = [Rescaling(), Dense()]

    def predict(self, sample, verbose=0):
        return self.output


def test_validate_loaded_model_accepts_batched_warmup_output() -> None:
    model = FakeModel(np.array([[0.2, 0.3, 0.4, 0.1]], dtype=np.float32))
    metadata = validate_loaded_model(
        model,
        input_size=settings.input_size,
        classes=list(settings.labels),
    )

    assert metadata["input_shape"] == [None, 224, 224, 3]
    assert metadata["output_shape"] == [None, 4]


def test_validate_loaded_model_rejects_wrong_internal_rescaling() -> None:
    model = FakeModel(np.array([[0.2, 0.3, 0.4, 0.1]], dtype=np.float32))

    class WrongRescaling:
        def get_config(self):
            return {"scale": 1 / 255, "offset": 0.0}

    model.layers[0] = WrongRescaling()
    with pytest.raises(ModelContractError, match="Rescaling"):
        validate_loaded_model(
            model,
            input_size=settings.input_size,
            classes=list(settings.labels),
        )


def test_validate_loaded_model_rejects_non_float32_input() -> None:
    model = FakeModel(np.array([[0.2, 0.3, 0.4, 0.1]], dtype=np.float32))
    model.inputs = [SimpleNamespace(dtype="float16")]

    with pytest.raises(ModelContractError, match="input type must be float32"):
        validate_loaded_model(
            model,
            input_size=settings.input_size,
            classes=list(settings.labels),
        )


def test_validate_loaded_model_rejects_non_finite_warmup_output() -> None:
    model = FakeModel(np.array([[np.nan, 0.5, 0.3, 0.2]], dtype=np.float32))

    with pytest.raises(ModelContractError, match="non-finite"):
        validate_loaded_model(
            model,
            input_size=settings.input_size,
            classes=list(settings.labels),
        )


def test_validate_loaded_model_rejects_non_canonical_class_order() -> None:
    model = FakeModel(np.array([[0.2, 0.3, 0.4, 0.1]], dtype=np.float32))

    with pytest.raises(ModelContractError, match="configured order"):
        validate_loaded_model(
            model,
            input_size=settings.input_size,
            classes=["brahman", "bali", "brangus", "limusin"],
        )


def test_validate_loaded_model_rejects_legacy_disease_class_order() -> None:
    model = FakeModel(np.array([[0.2, 0.3, 0.4, 0.1]], dtype=np.float32))

    with pytest.raises(ModelContractError, match="configured order"):
        validate_loaded_model(
            model,
            input_size=settings.input_size,
            classes=["FMD", "healthy", "LSD", "non_cattle"],
        )


def test_validate_loaded_model_rejects_missing_input_dtype() -> None:
    model = FakeModel(np.array([[0.2, 0.3, 0.4, 0.1]], dtype=np.float32))
    model.inputs = [SimpleNamespace()]

    with pytest.raises(ModelContractError, match="input type is unavailable"):
        validate_loaded_model(
            model,
            input_size=settings.input_size,
            classes=list(settings.labels),
        )
