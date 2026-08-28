from __future__ import annotations

from unittest.mock import Mock

import numpy as np
from inference_server import InferenceService
from PIL import Image


def test_predict_preserves_model_probabilities():
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
    assert result["prediction"]["disease_class"] == "healthy"
    assert result["prediction"]["confidence"] == 0.96
    assert result["prediction"]["is_reliable"] is True
    assert result["prediction"]["scores"] == {
        "FMD": 0.01,
        "healthy": 0.96,
        "LSD": 0.02,
        "non_cattle": 0.01,
    }
    assert result["prediction"]["outcome"] == "accepted"


def test_predict_marks_non_cattle_as_rejected() -> None:
    service = InferenceService.__new__(InferenceService)
    service.model_loader = Mock()
    service.model_loader.predict.return_value = np.array(
        [[0.01, 0.02, 0.01, 0.96]], dtype=np.float32
    )
    service.preprocessor = Mock()
    service.preprocessor.process.return_value = np.zeros(
        (1, 224, 224, 3), dtype=np.float32
    )

    result = service.predict(Image.new("RGB", (224, 224)))

    assert result["prediction"]["disease_class"] == "non_cattle"
    assert result["prediction"]["display_label_key"] == "validation.non_cattle"
    assert result["prediction"]["outcome"] == "rejected"
    assert result["prediction"]["is_reliable"] is False
    assert result["prediction"]["scores"]["non_cattle"] == 0.96
