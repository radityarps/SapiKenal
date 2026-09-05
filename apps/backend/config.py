import json
import os
from pathlib import Path

from pydantic_settings import (  # pyright: ignore[reportMissingImports]
    BaseSettings,
    SettingsConfigDict,
)

MODEL_CONTRACT_CLASSES: tuple[str, ...] = (
    "bali",
    "brahman",
    "brangus",
    "limusin",
)
MODEL_CONTRACT_VERSION = "sapikenal-jenis-sapi-mobilenetv3-contract-v1-fp32"

# Runtime labels for the active inference service.
CANONICAL_LABELS: tuple[str, ...] = MODEL_CONTRACT_CLASSES


def canonicalize_label(label: object) -> str:
    """Normalize model labels to the backend's canonical output contract."""
    normalized = str(label).strip().casefold().replace("-", "_").replace(" ", "_")
    return normalized


def _env_int(name: str, default: int) -> int:
    """Read an integer environment value with a clear configuration error."""
    raw_value = os.getenv(name, str(default))
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _load_labels(raw_path: str | None = None) -> list[str]:
    if raw_path is None:
        if "MODEL_CLASS_NAMES_PATH" not in os.environ:
            return list(CANONICAL_LABELS)
        raw_path = os.getenv("MODEL_CLASS_NAMES_PATH")
    if not raw_path:
        raise ValueError("MODEL_CLASS_NAMES_PATH is configured but empty")

    path = Path(raw_path)
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Model class names file is unavailable: {path}")

    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise TypeError("class names must be a JSON object")
        labels = [canonicalize_label(data[str(i)]) for i in range(len(data))]
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise ValueError(f"Invalid model class names file: {path}") from exc

    if labels != list(CANONICAL_LABELS):
        raise ValueError(
            "Model class names must match the canonical order: "
            + ", ".join(CANONICAL_LABELS)
        )
    return labels


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    # FastAPI
    fastapi_env: str = os.getenv("FASTAPI_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Model
    model_path: str = os.getenv("MODEL_PATH", "./model/best.keras")
    model_class_names_path: str | None = os.getenv("MODEL_CLASS_NAMES_PATH")
    device: str = os.getenv("DEVICE", "cpu")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")  # noqa: S104
    port: int = _env_int("PORT", 8000)
    workers: int = _env_int("WORKERS", 1)
    request_timeout: int = _env_int("REQUEST_TIMEOUT", 60)

    # Benchmark-only transport endpoints. Disabled unless explicitly enabled.
    benchmark_enabled: bool = os.getenv("BENCHMARK_ENABLED", "false").lower() == "true"

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # History sync metadata (kept separate from the admin DB).
    history_db_path: str = os.getenv("HISTORY_DB_PATH", "./data/history.sqlite3")
    allow_dev_db_reset: bool = (
        os.getenv("ALLOW_DEV_DB_RESET", "false").lower() == "true"
    )

    # Admin database and opaque server sessions
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/admin.sqlite3")
    session_ttl_days: int = _env_int("SESSION_TTL_DAYS", 7)
    password_min_length: int = _env_int("PASSWORD_MIN_LENGTH", 12)
    web_origin: str = os.getenv("WEB_ORIGIN", "http://localhost:5173")
    admin_device_hash_salt: str = os.getenv(
        "ADMIN_DEVICE_HASH_SALT", "development-device-mask"
    )
    model_registry_dir: str = os.getenv("MODEL_REGISTRY_DIR", "./model/registry")
    model_upload_max_bytes: int = _env_int("MODEL_UPLOAD_MAX_BYTES", 250_000_000)
    model_startup_fallback_enabled: bool = (
        os.getenv("MODEL_STARTUP_FALLBACK_ENABLED", "false").lower() == "true"
    )

    # Rate limiting
    rate_limit_max_requests: int = _env_int("RATE_LIMIT_MAX_REQUESTS", 10)
    rate_limit_window_seconds: int = _env_int("RATE_LIMIT_WINDOW_SECONDS", 60)

    # Model metadata
    model_version: str = os.getenv("MODEL_VERSION", MODEL_CONTRACT_VERSION)
    labels: list[str] = list(CANONICAL_LABELS)
    confidence_threshold: float = 0.60
    input_size: int = 224


settings = Settings()
settings.labels = _load_labels(settings.model_class_names_path)
