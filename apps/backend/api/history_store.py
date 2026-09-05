"""Tiny SQLite history store for mobile sync metadata."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from api.schemas import HistoryCreate
from config import settings

_LOCK = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS detection_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    local_id INTEGER,
    timestamp INTEGER NOT NULL,
    predicted_class TEXT NOT NULL,
    display_label TEXT NOT NULL,
    confidence REAL NOT NULL,
    scores TEXT NOT NULL,
    inference_mode TEXT NOT NULL,
    is_reliable INTEGER NOT NULL,
    processing_ms INTEGER,
    title TEXT,
    description TEXT,
    consent_status TEXT,
    app_version TEXT,
    model_version TEXT,
    image_source TEXT,
    preprocessing_summary TEXT,
    latitude REAL,
    longitude REAL,
    location_source TEXT,
    created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
    updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
    UNIQUE(device_id, local_id)
);
CREATE INDEX IF NOT EXISTS idx_detection_history_device_time
ON detection_history(device_id, timestamp DESC);
"""

COLUMNS = (
    "id",
    "device_id",
    "local_id",
    "timestamp",
    "predicted_class",
    "display_label",
    "confidence",
    "scores",
    "inference_mode",
    "is_reliable",
    "processing_ms",
    "title",
    "description",
    "consent_status",
    "app_version",
    "model_version",
    "image_source",
    "preprocessing_summary",
    "latitude",
    "longitude",
    "location_source",
    "created_at",
    "updated_at",
)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(detection_history)")}
    if columns and columns != set(COLUMNS):
        raise RuntimeError(
            "History database does not use the current breed schema; reset it in development before use"
        )


def _connect() -> sqlite3.Connection:
    path = Path(settings.history_db_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        existing = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'detection_history'"
        ).fetchone()
        if existing:
            _ensure_schema(conn)
        conn.executescript(SCHEMA)
        _ensure_schema(conn)
        conn.commit()
        return conn
    except (OSError, sqlite3.Error) as exc:
        raise RuntimeError("History store could not be initialized") from exc


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["is_reliable"] = bool(data["is_reliable"])
    return data


class HistoryStore:
    """Sync store for detection metadata. Image files stay on mobile."""

    # ponytail: SQLite fits TA demo/single VPS; move to PostgreSQL when concurrent writers/users grow.
    def __init__(self) -> None:
        self._conn = _connect()

    def upsert(self, item: dict[str, Any]) -> dict[str, Any]:
        item = HistoryCreate.model_validate(item).model_dump(mode="json")
        params = {
            **item,
            "scores": json.dumps(
                item["scores"], separators=(",", ":"), allow_nan=False
            ),
        }
        with _LOCK, self._conn:
            # Static SQL uses bound named parameters for every mobile value.
            # pi-lens-ignore: python-sql-injection
            self._conn.execute(
                """
                INSERT INTO detection_history (
                    device_id, local_id, timestamp, predicted_class, display_label,
                    confidence, scores, inference_mode, is_reliable, processing_ms,
                    title, description, consent_status,
                    app_version, model_version, image_source, preprocessing_summary,
                    latitude, longitude, location_source
                ) VALUES (
                    :device_id, :local_id, :timestamp, :predicted_class, :display_label,
                    :confidence, :scores, :inference_mode, :is_reliable, :processing_ms,
                    :title, :description, :consent_status,
                    :app_version, :model_version, :image_source, :preprocessing_summary,
                    :latitude, :longitude, :location_source
                )
                ON CONFLICT(device_id, local_id) DO UPDATE SET
                    timestamp=excluded.timestamp,
                    predicted_class=excluded.predicted_class,
                    display_label=excluded.display_label,
                    confidence=excluded.confidence,
                    scores=excluded.scores,
                    inference_mode=excluded.inference_mode,
                    is_reliable=excluded.is_reliable,
                    processing_ms=excluded.processing_ms,
                    title=excluded.title,
                    description=excluded.description,
                    consent_status=excluded.consent_status,
                    app_version=excluded.app_version,
                    model_version=excluded.model_version,
                    image_source=excluded.image_source,
                    preprocessing_summary=excluded.preprocessing_summary,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    location_source=excluded.location_source,
                    updated_at=unixepoch() * 1000
                """,
                params,
            )
            row = self._conn.execute(
                "SELECT * FROM detection_history WHERE device_id = ? AND local_id IS ? ORDER BY id DESC LIMIT 1",
                (params["device_id"], params["local_id"]),
            ).fetchone()
        return _row_to_dict(row)

    def list(self, device_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with _LOCK:
            rows = self._conn.execute(
                "SELECT * FROM detection_history WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?",
                (device_id, limit),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def delete(self, history_id: int, device_id: str) -> bool:
        with _LOCK, self._conn:
            cur = self._conn.execute(
                "DELETE FROM detection_history WHERE id = ? AND device_id = ?",
                (history_id, device_id),
            )
        return cur.rowcount > 0


history_store = HistoryStore()
