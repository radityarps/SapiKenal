"""Create the complete development schema without Alembic.

For a disposable local database only, set ``ALLOW_DEV_DB_RESET=true`` together
with ``FASTAPI_ENV=development`` and ``DEBUG=true`` before running this module.
Production databases are never reset by this script."""

import sqlite3
from pathlib import Path

from config import settings

_DROP_STATEMENTS = {
    "disease_contents": 'DROP TABLE "disease_contents"',
    "disease_content_revisions": 'DROP TABLE "disease_content_revisions"',
    "detection_history": 'DROP TABLE "detection_history"',
    "prediction_events": 'DROP TABLE "prediction_events"',
}


def _sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///") or ":memory:" in database_url:
        return None
    raw_path = database_url.removeprefix("sqlite:///")
    path = Path(raw_path)
    return path if path.is_absolute() else Path.cwd() / path


def _drop_tables(path: Path, table_names: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        for table in sorted(tables.intersection(table_names)):
            connection.execute(_DROP_STATEMENTS[table])
        connection.commit()


def _reset_incompatible_sqlite_tables() -> None:
    if not settings.allow_dev_db_reset:
        return
    if settings.fastapi_env != "development" or not settings.debug:
        raise RuntimeError(
            "Development database reset requires FASTAPI_ENV=development and DEBUG=true"
        )
    admin_path = _sqlite_path(settings.database_url)
    if admin_path is None:
        raise RuntimeError(
            "Development database reset requires a file-backed SQLite database"
        )
    _drop_tables(
        admin_path,
        {
            "disease_contents",
            "disease_content_revisions",
            "detection_history",
            "prediction_events",
        },
    )
    _drop_tables(configured_history_path(), {"detection_history"})


def configured_history_path() -> Path:
    path = Path(settings.history_db_path)
    return path if path.is_absolute() else Path.cwd() / path


def main() -> int:
    if settings.fastapi_env != "development" or not settings.debug:
        raise RuntimeError(
            "init_dev_db requires FASTAPI_ENV=development and DEBUG=true"
        )
    _reset_incompatible_sqlite_tables()
    # Import schema users only after the guarded reset has had a chance to run.
    import db.models  # noqa: F401 - register every model with Base.metadata
    from api import history_store  # noqa: F401 - initialize history store
    from db.base import Base
    from db.core import engine

    Base.metadata.create_all(bind=engine)
    reset_note = (
        "; incompatible legacy tables reset" if settings.allow_dev_db_reset else ""
    )
    print(f"Development database tables created or already present{reset_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
