from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient  # pyright: ignore[reportMissingImports]
from PIL import Image

from main import app


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), color="red").save(buf, format="JPEG")
    return buf.getvalue()


def test_predict_contract():
    result = {
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
    svc = MagicMock()
    svc.predict.return_value = result
    with (
        patch("api.prediction.is_model_ready", return_value=True),
        patch("api.prediction.get_inference_service", return_value=svc),
    ):
        response = TestClient(app).post(
            "/api/predict",
            files={"image": ("cow.jpg", _jpeg(), "image/jpeg")},
        )
    assert response.status_code == 200
    assert response.json() == result


def test_predict_keeps_low_confidence_as_success():
    result = {
        "status": "success",
        "prediction": {
            "predicted_class": "bali",
            "confidence": 0.31,
            "scores": {
                "bali": 0.31,
                "brahman": 0.30,
                "brangus": 0.29,
                "limusin": 0.10,
            },
        },
        "model_info": {"version": "four-class-test"},
        "processing_time_ms": 10,
        "preprocessing_time_ms": 4,
        "inference_time_ms": 6,
    }
    svc = MagicMock()
    svc.predict.return_value = result
    with (
        patch("api.prediction.is_model_ready", return_value=True),
        patch("api.prediction.get_inference_service", return_value=svc),
        patch("api.routes.record_prediction_event") as record_event,
    ):
        response = TestClient(app).post(
            "/api/predict",
            files={"image": ("low-confidence.jpg", _jpeg(), "image/jpeg")},
        )

    assert response.status_code == 200
    assert response.json() == result
    record_event.assert_called_once()
    assert record_event.call_args.kwargs["status"] == "success"
    assert record_event.call_args.kwargs["predicted_class"] == "bali"


def test_invalid_image_rejected():
    with patch("api.prediction.is_model_ready", return_value=True):
        response = TestClient(app).post(
            "/api/predict", files={"image": ("x.txt", b"x", "text/plain")}
        )
    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_IMAGE"


def test_history_sync_roundtrip(tmp_path, monkeypatch):
    db = tmp_path / "history.sqlite3"
    monkeypatch.setenv("HISTORY_DB_PATH", str(db))
    from config import settings

    settings.history_db_path = str(db)

    # Recreate store after env override.
    import importlib

    import api.history_store as history_store_mod
    import api.routes as routes_mod

    importlib.reload(history_store_mod)
    routes_mod.history_store = history_store_mod.history_store

    client = TestClient(app)
    scores = {
        "bali": 0.8,
        "brahman": 0.1,
        "brangus": 0.05,
        "limusin": 0.05,
    }
    payload = {
        "device_id": "device-12345678",
        "local_id": 7,
        "timestamp": 1710000000000,
        "predicted_class": "bali",
        "display_label": "Bali",
        "confidence": 0.8,
        "scores": scores,
        "inference_mode": "ONLINE",
        "is_reliable": True,
        "processing_ms": 12,
    }
    created = client.post("/api/history", json=payload)
    assert created.status_code == 200
    item = created.json()["item"]
    assert item["local_id"] == 7
    assert item["scores"] == scores
    assert "outcome" not in item
    assert "rejection_reason" not in item

    listed = client.get("/api/history", params={"device_id": "device-12345678"})
    assert listed.status_code == 200
    listed_item = listed.json()["items"][0]
    assert listed_item["predicted_class"] == "bali"
    assert listed_item["scores"] == scores

    deleted = client.delete(
        f"/api/history/{item['id']}", params={"device_id": "device-12345678"}
    )
    assert deleted.status_code == 200
    assert db.exists()


def test_history_rejects_legacy_disease_contract():
    client = TestClient(app)
    response = client.post(
        "/api/history",
        json={
            "device_id": "device-legacy-123456",
            "timestamp": 1710000000000,
            "predicted_class": "FMD",
            "display_label": "PMK",
            "confidence": 0.8,
            "scores": {"FMD": 0.8, "LSD": 0.1, "healthy": 0.1, "non_cattle": 0.0},
            "inference_mode": "ONLINE",
            "is_reliable": True,
        },
    )
    assert response.status_code == 422


def test_predict_does_not_persist_upload(tmp_path):
    before = set(Path(".").rglob("*.jpg"))
    svc = MagicMock()
    svc.predict.return_value = {
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
    with (
        patch("api.prediction.is_model_ready", return_value=True),
        patch("api.prediction.get_inference_service", return_value=svc),
    ):
        response = TestClient(app).post(
            "/api/predict",
            files={"image": ("cow.jpg", _jpeg(), "image/jpeg")},
        )
    after = set(Path(".").rglob("*.jpg"))
    assert response.status_code == 200
    assert after == before


def test_labels_follow_class_names_file(tmp_path, monkeypatch):
    class_names = tmp_path / "class_names.json"
    class_names.write_text('{"0":"Bali","1":"Brahman","2":"Brangus","3":"Limusin"}')
    monkeypatch.setenv("MODEL_CLASS_NAMES_PATH", str(class_names))

    import importlib

    import config as config_mod

    importlib.reload(config_mod)
    assert config_mod.settings.labels == ["bali", "brahman", "brangus", "limusin"]
