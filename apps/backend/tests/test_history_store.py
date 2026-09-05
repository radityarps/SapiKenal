from __future__ import annotations

import json
import sqlite3

import pytest
from sqlalchemy import create_engine, select  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker  # pyright: ignore[reportMissingImports]

import api.history_store as history_store_module
import services.audit as audit_module
from db.base import Base
from db.models import PredictionEvent


def _item(**overrides):
    item = {
        "device_id": "history-device-123456",
        "local_id": 3,
        "timestamp": 1_710_000_000_000,
        "predicted_class": "brangus",
        "display_label": "Brangus",
        "confidence": 0.8,
        "scores": {"bali": 0.05, "brahman": 0.1, "brangus": 0.8, "limusin": 0.05},
        "inference_mode": "OFFLINE",
        "is_reliable": True,
        "processing_ms": 22,
    }
    item.update(overrides)
    return item


def test_history_store_round_trips_labeled_scores(tmp_path):
    module = history_store_module
    original_path = module.settings.history_db_path
    module.settings.history_db_path = str(tmp_path / "history.sqlite3")
    try:
        store = module.HistoryStore()
        created = store.upsert(_item())
        assert created["predicted_class"] == "brangus"
        assert json.loads(created["scores"]) == _item()["scores"]

        updated = store.upsert(_item(title="updated"))
        assert updated["id"] == created["id"]
        assert updated["title"] == "updated"
        assert store.list("history-device-123456")[0]["id"] == created["id"]
        assert store.delete(created["id"], "history-device-123456")
        assert store.list("history-device-123456") == []
    finally:
        module.settings.history_db_path = original_path


def test_history_store_rejects_invalid_contract_before_write(tmp_path):
    module = history_store_module
    original_path = module.settings.history_db_path
    module.settings.history_db_path = str(tmp_path / "history.sqlite3")
    try:
        store = module.HistoryStore()
        with pytest.raises(
            ValueError, match="Scores must contain exactly four canonical model classes"
        ):
            store.upsert(_item(scores={"brangus": 1.0}))
    finally:
        module.settings.history_db_path = original_path


def test_history_store_rejects_incompatible_existing_schema(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE detection_history (id INTEGER PRIMARY KEY, outcome TEXT)"
        )

    module = history_store_module
    original_path = module.settings.history_db_path
    module.settings.history_db_path = str(path)
    try:
        with pytest.raises(RuntimeError, match="current breed schema"):
            module.HistoryStore()
    finally:
        module.settings.history_db_path = original_path


def test_history_schema_columns_are_explicit():
    assert "scores" in history_store_module.COLUMNS
    assert "outcome" not in history_store_module.COLUMNS
    assert "rejection_reason" not in history_store_module.COLUMNS


def test_history_values_rejects_malformed_scores():
    with pytest.raises(ValueError, match="Invalid history metadata"):
        audit_module._history_values(
            _item(scores={"bali": 2.0, "brahman": 0.0, "brangus": 0.0, "limusin": 0.0})
        )


def test_history_values_normalizes_enum_and_preserves_scores():
    values = audit_module._history_values(_item())
    assert values["predicted_class"] == "brangus"
    assert values["scores"] == _item()["scores"]


def test_prediction_event_drops_invalid_scores(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(audit_module, "SessionLocal", session_factory)
    audit_module.record_prediction_event(
        request_id="invalid-event",
        status="success",
        predicted_class="brangus",
        confidence=0.8,
        scores={"brangus": 0.8},
    )
    with session_factory() as db:
        event = db.scalar(
            select(PredictionEvent).where(PredictionEvent.request_id == "invalid-event")
        )
        assert event is not None
        assert event.scores is None
    engine.dispose()
