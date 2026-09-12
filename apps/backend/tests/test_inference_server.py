from __future__ import annotations

from unittest.mock import Mock

import numpy as np  # pyright: ignore[reportMissingImports]
import pytest  # pyright: ignore[reportMissingImports]
from PIL import Image

from inference_server import InferenceService


def test_predict_returns_breed_contract_without_rounding_scores():
	service = InferenceService.__new__(InferenceService)
	service.model_loader = Mock()
	service.model_loader.predict.return_value = np.array(
		[[0.01, 0.96, 0.01, 0.01, 0.005, 0.003, 0.002]], dtype=np.float32
	)
	service.preprocessor = Mock()
	service.preprocessor.process.return_value = np.zeros(
		(1, 224, 224, 3), dtype=np.float32
	)

	result = service.predict(Image.new("RGB", (224, 224)))

	assert result["status"] == "success"
	prediction = result["prediction"]
	assert prediction["predicted_class"] == "bali"
	assert prediction["confidence"] == pytest.approx(0.96)
	assert prediction["scores"] == pytest.approx(
		{
			"aceh": 0.01,
			"bali": 0.96,
			"limusin": 0.01,
			"madura": 0.01,
			"non_sapi": 0.005,
			"pasundan": 0.003,
			"po": 0.002,
		}
	)


def test_predict_keeps_low_confidence_as_success() -> None:
	service = InferenceService.__new__(InferenceService)
	service.model_loader = Mock()
	service.model_loader.predict.return_value = np.array(
		[[0.31, 0.30, 0.15, 0.10, 0.05, 0.05, 0.04]], dtype=np.float32
	)
	service.preprocessor = Mock()
	service.preprocessor.process.return_value = np.zeros(
		(1, 224, 224, 3), dtype=np.float32
	)

	result = service.predict(Image.new("RGB", (224, 224)))

	assert result["status"] == "success"
	assert result["prediction"]["predicted_class"] == "aceh"
	assert result["prediction"]["confidence"] == pytest.approx(0.31)
	assert result["prediction"]["scores"] == pytest.approx(
		{
			"aceh": 0.31,
			"bali": 0.30,
			"limusin": 0.15,
			"madura": 0.10,
			"non_sapi": 0.05,
			"pasundan": 0.05,
			"po": 0.04,
		}
	)
