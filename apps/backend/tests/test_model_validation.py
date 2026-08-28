from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from config import settings
from model.validation import (
    ModelContractError,
    validate_loaded_model,
)


class FakeModel:
    input_shape = (None, 224, 224, 3)
    output_shape = (None, 4)
    inputs = [SimpleNamespace(dtype="float32")]

    def __init__(self, output: np.ndarray) -> None:
        self.output = output

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
