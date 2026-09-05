from __future__ import annotations

from unittest.mock import Mock

import numpy as np  # pyright: ignore[reportMissingImports]
import pytest
from PIL import Image

from inference_server import InferenceService


def test_predict_returns_breed_contract_without_rounding_scores():
    service = InferenceService.__new__(InferenceService)
    service.model_loader = Mock()
    service.model_loader.predict.return_value = np.array(
        [[0.01, 0.96, 0.02, 0.01]], dtype=np.float32
    )
    service.preprocessor = Mock()
    service.preprocessor.process.return_value = np.zeros(
        (1, 224, 224, 3), dtype=np.float32
    )

    result = service.predict(Image.new("RGB", (224, 224)))

    assert result["status"] == "success"
    prediction = result["prediction"]
    assert prediction["predicted_class"] == "brahman"
    assert prediction["confidence"] == pytest.approx(0.96)
    assert prediction["scores"] == pytest.approx(
        {
            "bali": 0.01,
            "brahman": 0.96,
            "brangus": 0.02,
            "limusin": 0.01,
        }
    )


def test_predict_keeps_low_confidence_as_success() -> None:
    service = InferenceService.__new__(InferenceService)
    service.model_loader = Mock()
    service.model_loader.predict.return_value = np.array(
        [[0.31, 0.30, 0.29, 0.10]], dtype=np.float32
    )
    service.preprocessor = Mock()
    service.preprocessor.process.return_value = np.zeros(
        (1, 224, 224, 3), dtype=np.float32
    )

    result = service.predict(Image.new("RGB", (224, 224)))

    assert result["status"] == "success"
    assert result["prediction"]["predicted_class"] == "bali"
    assert result["prediction"]["confidence"] == pytest.approx(0.31)
    assert result["prediction"]["scores"] == pytest.approx(
        {
            "bali": 0.31,
            "brahman": 0.30,
            "brangus": 0.29,
            "limusin": 0.10,
        }
    )
