from __future__ import annotations

import argparse
import io
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException  # pyright: ignore[reportMissingImports]
from fastapi.testclient import TestClient  # pyright: ignore[reportMissingImports]
from PIL import Image
from starlette.websockets import (
    WebSocketDisconnect,  # pyright: ignore[reportMissingImports]
)

from benchmark_transport import (
    ImageFixture,
    Observation,
    comparable_prediction_contract,
    write_artifacts,
)
from config import settings
from main import app


def _jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color="red").save(buffer, format="JPEG")
    return buffer.getvalue()


def _prediction_result() -> dict:
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


def test_benchmark_endpoints_are_hidden_before_request_validation(monkeypatch):
    monkeypatch.setattr(settings, "benchmark_enabled", False)
    client = TestClient(app)

    response = client.post("/api/benchmark/predict")
    assert response.status_code == 404

    with (
        pytest.raises(WebSocketDisconnect) as exception,
        client.websocket_connect("/api/benchmark/ws"),
    ):
        pass
    assert exception.value.code == 1008


def test_benchmark_predict_has_equivalent_rest_and_websocket_outputs(monkeypatch):
    monkeypatch.setattr(settings, "benchmark_enabled", True)
    result = _prediction_result()
    mocked_prediction = AsyncMock(return_value=(result, 12.5))

    with patch("api.routes.predict_image_bytes", mocked_prediction):
        client = TestClient(app)
        rest_response = client.post(
            "/api/benchmark/predict",
            files={"image": ("cow.jpg", _jpeg(), "image/jpeg")},
        )
        with client.websocket_connect("/api/benchmark/ws") as websocket:
            websocket.send_json({"operation": "predict", "content_type": "image/jpeg"})
            websocket.send_bytes(_jpeg())
            websocket_response = websocket.receive_json()

    expected = {**result, "benchmark": {"server_processing_ms": 12.5}}
    assert rest_response.status_code == 200
    assert rest_response.json() == expected
    assert websocket_response == expected
    assert mocked_prediction.await_count == 2


def test_benchmark_echo_has_equivalent_rest_and_websocket_outputs(monkeypatch):
    monkeypatch.setattr(settings, "benchmark_enabled", True)
    payload = b"benchmark-payload"
    client = TestClient(app)

    rest_response = client.post(
        "/api/benchmark/echo",
        files={"payload": ("payload.bin", payload, "application/octet-stream")},
    )
    with client.websocket_connect("/api/benchmark/ws") as websocket:
        websocket.send_json({"operation": "echo"})
        websocket.send_bytes(payload)
        websocket_response = websocket.receive_json()

    assert rest_response.status_code == 200
    assert rest_response.json()["status"] == "success"
    assert websocket_response["status"] == "success"
    assert rest_response.json()["payload_size_bytes"] == len(payload)
    assert websocket_response["payload_size_bytes"] == len(payload)


def test_benchmark_rest_and_websocket_share_error_envelope(monkeypatch):
    monkeypatch.setattr(settings, "benchmark_enabled", True)

    with patch(
        "api.routes.predict_image_bytes",
        AsyncMock(
            side_effect=HTTPException(status_code=422, detail="Invalid image file")
        ),
    ):
        client = TestClient(app)
        rest_response = client.post(
            "/api/benchmark/predict",
            files={"image": ("cow.jpg", _jpeg(), "image/jpeg")},
        )
        with client.websocket_connect("/api/benchmark/ws") as websocket:
            websocket.send_json({"operation": "predict", "content_type": "image/jpeg"})
            websocket.send_bytes(_jpeg())
            websocket_response = websocket.receive_json()

    expected = {
        "status": "error",
        "error_code": "INVALID_IMAGE",
        "message": "Invalid image file",
    }
    assert rest_response.status_code == 422
    assert rest_response.json() == expected
    assert websocket_response == expected


def test_prediction_contract_comparison_excludes_dynamic_timings():
    rest_response = {
        **_prediction_result(),
        "processing_time_ms": 20,
        "preprocessing_time_ms": 4,
        "inference_time_ms": 16,
        "benchmark": {"server_processing_ms": 20.1},
    }
    websocket_response = {
        **_prediction_result(),
        "processing_time_ms": 35,
        "preprocessing_time_ms": 5,
        "inference_time_ms": 30,
        "benchmark": {"server_processing_ms": 35.2},
    }

    assert comparable_prediction_contract(
        rest_response
    ) == comparable_prediction_contract(websocket_response)


def test_write_artifacts_serializes_path_arguments(tmp_path):
    fixture_path = tmp_path / "cow.jpg"
    fixture_path.write_bytes(b"test-image")
    fixture = ImageFixture(
        path=fixture_path,
        content_type="image/jpeg",
        payload=b"test-image",
        sha256="abc123",
    )
    observation = Observation(
        scenario="echo",
        protocol="REST API",
        iteration=1,
        image_name="cow.jpg",
        payload_size_bytes=fixture.size_bytes,
        total_ms=1.5,
        server_processing_ms=0.5,
        communication_estimate_ms=1.0,
        connection_setup_ms=None,
        success=True,
        error="",
    )
    args = argparse.Namespace(
        base_url="http://127.0.0.1:8000",
        images=[fixture_path],
        output_dir=tmp_path,
        warmups=10,
        iterations=30,
        scenarios=["echo"],
    )

    write_artifacts(tmp_path, [fixture], [observation], [], args)

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["arguments"]["images"] == [str(fixture_path)]
    assert manifest["arguments"]["output_dir"] == str(tmp_path)
