import hashlib
import time
from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import main as backend_main
from api import admin_routes
from api.auth_security import hash_password, issue_session
from config import settings
from db.base import Base
from db.core import get_db
from db.models import (
    DetectionHistory,
    ModelActivation,
    ModelVersion,
    PredictionEvent,
    User,
)
from main import app


@pytest.fixture()
def admin_client() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as db:
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("A-strong-admin-password"),
            display_name="Test Admin",
            role="admin",
            status="active",
        )
        db.add(admin)
        db.flush()
        token, _ = issue_session(db, admin, user_agent="test", ip_hash=None)
        db.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client, session_factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_dashboard_and_user_guardrails(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = admin_client
    dashboard = client.get("/api/admin/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["users"]["active"] == 1

    created = client.post(
        "/api/admin/users",
        json={
            "email": "operator@example.com",
            "display_name": "Operator",
            "role": "user",
            "password": "A-strong-operator-password",
        },
    )
    assert created.status_code == 201
    assert created.json()["user"]["role"] == "user"
    assert client.get("/api/admin/users").json()["total"] == 2

    audit_items = client.get("/api/admin/audit-logs").json()["items"]
    assert audit_items[0]["actor_display_name"] == "Test Admin"
    assert client.get("/api/admin/audit-logs?search=Test%20Admin").json()["total"] == 1
    assert client.get("/api/admin/audit-logs?search=tidak-ada").json()["total"] == 0

    admin_id = client.get("/api/auth/me").json()["user"]["id"]
    self_demotion = client.patch(
        f"/api/admin/users/{admin_id}",
        json={"role": "user"},
    )
    assert self_demotion.status_code == 409


def test_dashboard_and_predictions_use_breed_status_and_scores(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = admin_client
    timestamp = round(time.time() * 1_000)
    bali_scores = {"bali": 0.91, "brahman": 0.04, "brangus": 0.03, "limusin": 0.02}
    brahman_scores = {"bali": 0.05, "brahman": 0.85, "brangus": 0.05, "limusin": 0.05}
    with session_factory() as db:
        db.add(
            DetectionHistory(
                device_id="accepted-device-123456",
                local_id=1,
                timestamp=timestamp,
                predicted_class="bali",
                display_label="Bali",
                confidence=0.91,
                scores=bali_scores,
                inference_mode="online",
                is_reliable=True,
            )
        )
        db.add(
            PredictionEvent(
                request_id="failed-request",
                status="failed",
                error_code="MODEL_NOT_READY",
            )
        )
        db.add(
            PredictionEvent(
                request_id="direct-request",
                status="success",
                predicted_class="brahman",
                confidence=0.85,
                scores=brahman_scores,
                processing_ms=90,
                model_version="four-class-v1",
            )
        )
        db.commit()

    dashboard = client.get("/api/admin/dashboard").json()["predictions"]
    assert dashboard["attempts"] == 3
    assert dashboard["accepted"] == 2
    assert dashboard["failures"] == 1
    assert dashboard["distribution"] == {
        "bali": 1,
        "brahman": 1,
        "brangus": 0,
        "limusin": 0,
    }
    assert "rejected_non_cattle" not in dashboard

    successful = client.get(
        "/api/admin/predictions",
        params={"status": "success", "predicted_class": "brahman"},
    ).json()
    assert successful["total"] == 1
    assert successful["items"][0]["scores"]["brahman"] == 0.85
    assert "outcome" not in successful["items"][0]

    failed = client.get("/api/admin/predictions", params={"status": "failed"}).json()
    assert failed["total"] == 1
    assert failed["items"][0]["status"] == "failed"
    assert failed["items"][0]["error_code"] == "MODEL_NOT_READY"


def test_dashboard_deduplicates_online_event_mirrored_by_mobile_history(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = admin_client
    timestamp = round(time.time() * 1_000)
    scores = {"bali": 0.91, "brahman": 0.02, "brangus": 0.05, "limusin": 0.02}
    with session_factory() as db:
        db.add(
            DetectionHistory(
                device_id="synced-device-123456",
                local_id=17,
                timestamp=timestamp,
                predicted_class="bali",
                display_label="Bali",
                confidence=0.91,
                scores=scores,
                inference_mode="online",
                is_reliable=True,
                processing_ms=90,
                model_version="four-class-v1",
            )
        )
        db.add(
            PredictionEvent(
                request_id="mirrored-online-request",
                status="success",
                predicted_class="bali",
                confidence=0.91,
                scores=scores,
                processing_ms=90,
                model_version="four-class-v1",
                created_at=datetime.fromtimestamp(timestamp / 1_000, timezone.utc),
            )
        )
        db.commit()

    predictions = client.get("/api/admin/dashboard").json()["predictions"]
    assert predictions["attempts"] == 1
    assert predictions["accepted"] == 1

    listed = client.get("/api/admin/predictions").json()
    assert listed["total"] == 1
    assert listed["items"][0]["status"] == "success"


def test_last_admin_guard_and_prediction_masking(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = admin_client
    with session_factory() as db:
        admin = db.scalar(select(User).where(User.email == "admin@example.com"))
        assert admin is not None
        db.add(
            DetectionHistory(
                device_id="raw-device-id-123456",
                local_id=1,
                timestamp=1_725_000_000_000,
                predicted_class="bali",
                display_label="Bali",
                confidence=0.91,
                scores={
                    "bali": 0.91,
                    "brahman": 0.04,
                    "brangus": 0.03,
                    "limusin": 0.02,
                },
                inference_mode="online",
                is_reliable=True,
                processing_ms=30,
                app_version="1.0.0",
                model_version="test-model",
                user_id=admin.id,
            )
        )
        db.commit()

    me = client.get("/api/auth/me").json()["user"]["id"]
    guarded = client.patch(f"/api/admin/users/{me}", json={"status": "inactive"})
    assert guarded.status_code == 409

    predictions = client.get("/api/admin/predictions").json()
    assert predictions["total"] == 1
    assert predictions["items"][0]["device_ref"] != "raw-device-id-123456"
    assert len(predictions["items"][0]["device_ref"]) == 8
    assert client.get("/api/admin/predictions?search=Bali").json()["total"] == 1
    assert client.get("/api/admin/predictions?search=PMK").json()["total"] == 0


def test_breed_profile_lifecycle_and_public_read(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = admin_client
    payload = {
        "slug": "bali",
        "model_class": "bali",
        "display_name": "Bali",
        "summary": "Profil sapi Bali.",
        "strengths": "Adaptif terhadap lingkungan tropis.",
        "limitations": "Perlu pakan dan perawatan sesuai kondisi.",
        "disclaimer": "Profil informatif, bukan penilaian peternakan final.",
        "locale": "id-ID",
    }
    created = client.post("/api/admin/profiles", json=payload)
    assert created.status_code == 201
    profile_id = created.json()["item"]["id"]
    assert client.post(f"/api/admin/profiles/{profile_id}/activate").status_code == 200
    public = client.get("/api/content/profiles")
    assert public.status_code == 200
    assert public.json()["items"][0]["slug"] == "bali"
    assert "strengths" in public.json()["items"][0]
    assert "limitations" in public.json()["items"][0]
    assert (
        client.post(f"/api/admin/profiles/{profile_id}/deactivate").status_code == 200
    )
    assert client.get("/api/content/profiles").json()["items"] == []


def test_model_registration_rejects_missing_allowlisted_artifact(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = admin_client
    response = client.post(
        "/api/admin/models/register",
        json={
            "version": "candidate-1",
            "artifact_name": "candidate.keras",
            "checksum": "0" * 64,
            "classes": ["bali", "brahman", "brangus", "limusin"],
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "MODEL_ARTIFACT_INVALID"


def test_enabled_startup_fallback_registers_active_model_metadata(
    admin_client: tuple[TestClient, sessionmaker[Session]],
    tmp_path,
    monkeypatch,
) -> None:
    _, session_factory = admin_client
    source = tmp_path / "fallback.keras"
    source.write_bytes(b"fallback-model")
    registry = tmp_path / "registry"
    monkeypatch.setattr(settings, "model_path", str(source))
    monkeypatch.setattr(settings, "model_registry_dir", str(registry))
    monkeypatch.setattr(settings, "model_startup_fallback_enabled", True)
    monkeypatch.setattr(backend_main, "SessionLocal", session_factory)
    monkeypatch.setattr(backend_main, "reload_active_model", lambda *args: None)
    monkeypatch.setattr(
        backend_main,
        "validate_model_file",
        lambda path, *, input_size, classes: {
            "checksum": hashlib.sha256(path.read_bytes()).hexdigest()
        },
    )

    backend_main._restore_active_model_from_registry()

    with session_factory() as db:
        model = db.scalar(select(ModelVersion))
        assert model is not None
        assert model.version == settings.model_version
        assert model.status == "active"
        assert model.checksum == hashlib.sha256(source.read_bytes()).hexdigest()
        assert model.classes == list(settings.labels)
        assert model.input_size == settings.input_size
        assert (registry / model.artifact_name).read_bytes() == source.read_bytes()


def test_model_upload_registers_available_artifact_without_activation(
    admin_client: tuple[TestClient, sessionmaker[Session]],
    tmp_path,
    monkeypatch,
) -> None:
    client, _ = admin_client
    registry = tmp_path / "registry"
    monkeypatch.setattr(settings, "model_registry_dir", str(registry))

    def fake_validate(path, *, input_size, classes):
        return {
            "checksum": hashlib.sha256(path.read_bytes()).hexdigest(),
            "input_shape": [None, input_size, input_size, 3],
            "output_shape": [None, len(classes)],
            "classes": classes,
        }

    monkeypatch.setattr(admin_routes, "validate_model_file", fake_validate)
    response = client.post(
        "/api/admin/models/upload",
        data={
            "version": "candidate-upload-1",
            "input_size": "224",
            "classes": "bali,brahman,brangus,limusin",
            "notes": "Candidate upload test",
        },
        files={
            "artifact": (
                "candidate.keras",
                b"test-model-bytes",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 201
    item = response.json()["item"]
    assert item["status"] == "available"
    assert item["checksum"] == hashlib.sha256(b"test-model-bytes").hexdigest()
    assert (registry / item["artifact_name"]).read_bytes() == b"test-model-bytes"
    assert (
        client.get("/api/admin/models").json()["active_version"]
        == settings.model_version
    )
    models = client.get("/api/admin/models").json()
    assert models["total"] == 1
    assert models["items"][0]["version"] == "candidate-upload-1"


def test_model_upload_rejects_filename_path_separator(
    admin_client: tuple[TestClient, sessionmaker[Session]],
    tmp_path,
    monkeypatch,
) -> None:
    client, _ = admin_client
    registry = tmp_path / "registry"
    monkeypatch.setattr(settings, "model_registry_dir", str(registry))

    response = client.post(
        "/api/admin/models/upload",
        data={"version": "candidate-traversal"},
        files={
            "artifact": (
                "../candidate.keras",
                b"not-a-model",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "MODEL_FILE_NAME_INVALID"
    assert not registry.exists()


def test_model_activation_and_rollback_keep_one_active_version(
    admin_client: tuple[TestClient, sessionmaker[Session]],
    tmp_path,
    monkeypatch,
) -> None:
    client, session_factory = admin_client
    registry = tmp_path / "registry"
    registry.mkdir()
    monkeypatch.setattr(settings, "model_registry_dir", str(registry))

    first_bytes = b"first-model"
    second_bytes = b"second-model"
    first_name = "candidate-first.keras"
    second_name = "candidate-second.keras"
    (registry / first_name).write_bytes(first_bytes)
    (registry / second_name).write_bytes(second_bytes)
    with session_factory() as db:
        admin = db.scalar(select(User).where(User.email == "admin@example.com"))
        assert admin is not None
        first = ModelVersion(
            version="candidate-first",
            artifact_name=first_name,
            checksum=hashlib.sha256(first_bytes).hexdigest(),
            status="available",
            input_size=settings.input_size,
            classes=list(settings.labels),
            registered_by=admin.id,
        )
        second = ModelVersion(
            version="candidate-second",
            artifact_name=second_name,
            checksum=hashlib.sha256(second_bytes).hexdigest(),
            status="available",
            input_size=settings.input_size,
            classes=list(settings.labels),
            registered_by=admin.id,
        )
        db.add_all([first, second])
        db.commit()
        first_id = first.id
        second_id = second.id

    monkeypatch.setattr(admin_routes, "reload_active_model", lambda *args: None)
    first_response = client.post(
        f"/api/admin/models/{first_id}/activate",
        json={"reason": "Initial candidate"},
    )
    assert first_response.status_code == 200
    second_response = client.post(
        f"/api/admin/models/{second_id}/activate",
        json={"reason": "Replace candidate"},
    )
    assert second_response.status_code == 200
    rollback_response = client.post(
        f"/api/admin/models/{first_id}/rollback",
        json={"reason": "Restore prior candidate"},
    )
    assert rollback_response.status_code == 200

    models = client.get("/api/admin/models").json()
    statuses = {item["version"]: item["status"] for item in models["items"]}
    assert statuses == {"candidate-first": "active", "candidate-second": "retired"}
    assert models["active_version"] == "candidate-first"
    by_version = {item["version"]: item for item in models["items"]}
    assert by_version["candidate-first"]["rolled_back_at"] is not None
    assert by_version["candidate-second"]["deactivated_at"] is not None
    with session_factory() as db:
        active_count = db.scalar(
            select(ModelVersion.id).where(ModelVersion.status == "active")
        )
        assert active_count == first_id
        activations = db.scalars(
            select(ModelActivation).where(ModelActivation.status == "success")
        ).all()
        assert len(activations) == 3


def test_failed_model_activation_keeps_candidate_inactive_and_audited(
    admin_client: tuple[TestClient, sessionmaker[Session]],
    tmp_path,
    monkeypatch,
) -> None:
    client, session_factory = admin_client
    registry = tmp_path / "registry"
    registry.mkdir()
    monkeypatch.setattr(settings, "model_registry_dir", str(registry))
    payload = b"candidate-model"
    artifact_name = "candidate-failure.keras"
    (registry / artifact_name).write_bytes(payload)
    with session_factory() as db:
        admin = db.scalar(select(User).where(User.email == "admin@example.com"))
        assert admin is not None
        model = ModelVersion(
            version="candidate-failure",
            artifact_name=artifact_name,
            checksum=hashlib.sha256(payload).hexdigest(),
            status="available",
            input_size=settings.input_size,
            classes=list(settings.labels),
            registered_by=admin.id,
        )
        db.add(model)
        db.commit()
        model_id = model.id

    def fail_reload(*args):
        raise RuntimeError("candidate warm-up failed")

    monkeypatch.setattr(admin_routes, "reload_active_model", fail_reload)
    response = client.post(
        f"/api/admin/models/{model_id}/activate",
        json={"reason": "Reject bad candidate"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "MODEL_ACTIVATION_FAILED"
    item = client.get(f"/api/admin/models/{model_id}").json()["item"]
    assert item["status"] == "available"
    assert (
        client.get("/api/admin/audit-logs?action=model_activate_failed").json()["total"]
        == 1
    )
