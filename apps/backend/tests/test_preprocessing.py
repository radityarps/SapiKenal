from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import numpy as np  # pyright: ignore[reportMissingImports]
from fastapi.testclient import TestClient  # pyright: ignore[reportMissingImports]
from PIL import Image

from main import app
from preprocessing.model_preprocessor import ModelPreprocessor


def _success_response():
    return {
        "status": "success",
        "prediction": {
            "predicted_class": "bali",
            "confidence": 0.9,
            "scores": {
                "bali": 0.9,
                "brahman": 0.05,
                "brangus": 0.04,
                "limusin": 0.01,
            },
        },
        "model_info": {"version": "test"},
        "processing_time_ms": 10,
        "preprocessing_time_ms": 4,
        "inference_time_ms": 6,
    }


def test_model_preprocessor_uses_bilinear_resize():
    source = Image.new("RGB", (3, 2))
    source.putdata(
        [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (0, 255, 255),
            (255, 0, 255),
        ]
    )

    actual = ModelPreprocessor.process(source)[0]
    expected = np.asarray(
        source.resize((224, 224), Image.Resampling.BILINEAR), dtype=np.float32
    )

    assert actual.shape == (224, 224, 3)
    assert actual.dtype == np.float32
    assert np.array_equal(actual, expected)


def _predict_exif_image(orientation: int, image: Image.Image):
    exif = Image.Exif()
    exif[274] = orientation
    payload = io.BytesIO()
    image.save(payload, format="PNG", exif=exif)

    service = MagicMock()
    service.predict.return_value = _success_response()
    with (
        patch("api.prediction.is_model_ready", return_value=True),
        patch("api.prediction.get_inference_service", return_value=service),
    ):
        response = TestClient(app).post(
            "/api/predict",
            files={"image": ("oriented.png", payload.getvalue(), "image/png")},
        )

    assert response.status_code == 200
    return service.predict.call_args.args[0]


def test_predict_transposes_exif_orientation_before_inference():
    image = Image.new("RGB", (2, 3), color="red")

    received = _predict_exif_image(6, image)

    assert received.size == (3, 2)


def test_predict_mirrors_exif_orientation_before_inference():
    image = Image.new("RGB", (2, 1))
    image.putdata([(255, 0, 0), (0, 0, 255)])

    received = _predict_exif_image(2, image)

    assert received.size == (2, 1)
    assert received.getpixel((0, 0)) == (0, 0, 255)
    assert received.getpixel((1, 0)) == (255, 0, 0)
