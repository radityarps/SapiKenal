import hashlib
import time
from collections.abc import Generator
from datetime import datetime, timezone

import pytest  # pyright: ignore[reportMissingImports]
from fastapi.testclient import TestClient  # pyright: ignore[reportMissingImports]
from sqlalchemy import (  # pyright: ignore[reportMissingImports]
    create_engine,
    select,
)
from sqlalchemy.orm import (  # pyright: ignore[reportMissingImports]
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool  # pyright: ignore[reportMissingImports]

import main as backend_main
from api import admin_routes
from api.auth_security import hash_password, issue_session
from config import settings
from db.base import Base
from db.core import get_db
from db.models import (
    DetectionHistory,
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
    bali_scores = {
        "aceh": 0.02,
        "bali": 0.90,
        "limusin": 0.02,
        "madura": 0.02,
        "non_sapi": 0.01,
        "pasundan": 0.02,
        "po": 0.01,
    }
    madura_scores = {
        "aceh": 0.03,
        "bali": 0.03,
        "limusin": 0.03,
        "madura": 0.82,
        "non_sapi": 0.03,
        "pasundan": 0.03,
        "po": 0.03,
    }
    with session_factory() as db:
        db.add(
            DetectionHistory(
                device_id="accepted-device-123456",
                local_id=1,
                timestamp=timestamp,
                predicted_class="bali",
                display_label="Bali",
                confidence=0.90,
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
                predicted_class="madura",
                confidence=0.82,
                scores=madura_scores,
                processing_ms=90,
                model_version="seven-class-v2",
            )
        )
        db.commit()

    dashboard = client.get("/api/admin/dashboard").json()["predictions"]
    assert dashboard["attempts"] == 3
    assert dashboard["accepted"] == 2
    assert dashboard["failures"] == 1
    assert dashboard["distribution"] == {
        "aceh": 0,
        "bali": 1,
        "limusin": 0,
        "madura": 1,
        "non_sapi": 0,
        "pasundan": 0,
        "po": 0,
    }
    assert set(dashboard["distribution"]) == {
        "aceh",
        "bali",
        "limusin",
        "madura",
        "non_sapi",
        "pasundan",
        "po",
    }
    assert "rejected_non_cattle" not in dashboard
    assert "low_confidence" not in dashboard
    assert "low_confidence_rate" not in dashboard
    assert dashboard["average_confidence"] == pytest.approx(0.86)

    successful = client.get(
        "/api/admin/predictions",
        params={"status": "success", "predicted_class": "madura"},
    ).json()
    assert successful["total"] == 1
    assert successful["items"][0]["scores"]["madura"] == 0.82
    assert "outcome" not in successful["items"][0]
    assert "is_reliable" not in successful["items"][0]

    failed = client.get("/api/admin/predictions", params={"status": "failed"}).json()
    assert failed["total"] == 1
    assert failed["items"][0]["status"] == "failed"
    assert failed["items"][0]["error_code"] == "MODEL_NOT_READY"


def test_dashboard_deduplicates_online_event_mirrored_by_mobile_history(
    admin_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = admin_client
    timestamp = round(time.time() * 1_000)
    scores = {
        "aceh": 0.02,
        "bali": 0.90,
        "limusin": 0.02,
        "madura": 0.02,
        "non_sapi": 0.01,
        "pasundan": 0.02,
        "po": 0.01,
    }
    with session_factory() as db:
        db.add(
            DetectionHistory(
                device_id="synced-device-123456",
                local_id=17,
                timestamp=timestamp,
                predicted_class="bali",
                display_label="Bali",
                confidence=0.90,
                scores=scores,
                inference_mode="online",
                is_reliable=True,
                processing_ms=90,
                model_version="seven-class-v2",
            )
        )
        db.add(
            PredictionEvent(
                request_id="mirrored-online-request",
                status="success",
                predicted_class="bali",
                confidence=0.90,
                scores=scores,
                processing_ms=90,
                model_version="seven-class-v2",
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
                confidence=0.90,
                scores={
                    "aceh": 0.02,
                    "bali": 0.90,
                    "limusin": 0.02,
                    "madura": 0.02,
                    "non_sapi": 0.01,
                    "pasundan": 0.02,
                    "po": 0.01,
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


def test_static_model_loading(
    tmp_path,
    monkeypatch,
) -> None:
    source = tmp_path / "model.keras"
    source.write_bytes(b"static-model")
    monkeypatch.setattr(settings, "model_path", str(source))
    reloaded: list[tuple] = []
    monkeypatch.setattr(
        backend_main,
        "reload_active_model",
        lambda path, version, classes, input_size: reloaded.append((path, version)),
    )

    backend_main._load_static_model()
    assert len(reloaded) == 1
    assert reloaded[0][0] == source
    assert reloaded[0][1] == settings.model_version


def test_static_model_loading_missing_file(
    tmp_path,
    monkeypatch,
) -> None:
    source = tmp_path / "nonexistent.keras"
    monkeypatch.setattr(settings, "model_path", str(source))
    unavailable_reasons: list[str] = []
    monkeypatch.setattr(
        backend_main,
        "mark_model_unavailable",
        lambda reason: unavailable_reasons.append(reason),
    )

    backend_main._load_static_model()
    assert len(unavailable_reasons) == 1
    assert "unavailable" in unavailable_reasons[0].lower()

