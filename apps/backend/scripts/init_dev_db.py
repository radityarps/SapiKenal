"""Create the complete development schema without Alembic."""

import db.models  # noqa: F401 - register every model with Base.metadata
from api import history_store  # noqa: F401 - create the legacy mobile history table
from config import settings
from db.base import Base
from db.core import engine


def main() -> int:
    if settings.fastapi_env != "development" or not settings.debug:
        raise RuntimeError(
            "init_dev_db requires FASTAPI_ENV=development and DEBUG=true"
        )
    Base.metadata.create_all(bind=engine)
    print("Development database tables created or already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
