from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from config import CANONICAL_LABELS, _load_labels
from scripts import init_dev_db  # pyright: ignore[reportAttributeAccessIssue]


def _legacy_tables(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE detection_history (id INTEGER PRIMARY KEY, score_fmd REAL);
            CREATE TABLE prediction_events (id TEXT PRIMARY KEY, outcome TEXT);
            CREATE TABLE disease_contents (id TEXT PRIMARY KEY);
            CREATE TABLE disease_content_revisions (id TEXT PRIMARY KEY);
            """
        )
        connection.commit()


def _tables(path: Path) -> set[str]:
    with sqlite3.connect(path) as connection:
        return {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }


def test_explicit_missing_class_names_file_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_CLASS_NAMES_PATH", str(tmp_path / "missing.json"))

    with pytest.raises(ValueError, match="unavailable"):
        _load_labels()


def test_unset_class_names_file_uses_canonical_defaults(monkeypatch):
    monkeypatch.delenv("MODEL_CLASS_NAMES_PATH", raising=False)

    assert _load_labels() == list(CANONICAL_LABELS)


def test_0005_migration_is_immutable_relative_to_head():
    import hashlib
    import subprocess

    path = (
        Path(__file__).parents[1]
        / "alembic/versions/0005_four_class_prediction_contract.py"
    )
    expected = subprocess.run(
        [
            "git",
            "show",
            "HEAD:apps/backend/alembic/versions/0005_four_class_prediction_contract.py",
        ],
        check=True,
        capture_output=True,
    ).stdout
    assert (
        hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(expected).digest()
    )


def test_dev_reset_clears_both_sqlite_stores(monkeypatch, tmp_path):
    admin_path = tmp_path / "admin.sqlite3"
    history_path = tmp_path / "history.sqlite3"
    _legacy_tables(admin_path)
    with sqlite3.connect(history_path) as connection:
        connection.execute(
            "CREATE TABLE detection_history (id INTEGER PRIMARY KEY, score_fmd REAL)"
        )
        connection.commit()

    monkeypatch.setattr(init_dev_db.settings, "allow_dev_db_reset", True)
    monkeypatch.setattr(
        init_dev_db.settings,
        "database_url",
        f"sqlite:///{admin_path}",
    )
    monkeypatch.setattr(init_dev_db.settings, "history_db_path", str(history_path))
    init_dev_db._reset_incompatible_sqlite_tables()

    assert _tables(admin_path) == set()
    assert (
        _tables(history_path) == {"sqlite_sequence"} or _tables(history_path) == set()
    )


def test_dev_reset_is_disabled_by_default(monkeypatch, tmp_path):
    admin_path = tmp_path / "admin.sqlite3"
    _legacy_tables(admin_path)
    monkeypatch.setattr(init_dev_db.settings, "allow_dev_db_reset", False)
    monkeypatch.setattr(
        init_dev_db.settings,
        "database_url",
        f"sqlite:///{admin_path}",
    )
    monkeypatch.setattr(
        init_dev_db.settings, "history_db_path", str(tmp_path / "history.sqlite3")
    )

    init_dev_db._reset_incompatible_sqlite_tables()

    assert _tables(admin_path) == {
        "detection_history",
        "prediction_events",
        "disease_contents",
        "disease_content_revisions",
    }
