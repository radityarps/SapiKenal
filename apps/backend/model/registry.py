"""Filesystem helpers for the private backend model registry."""

from __future__ import annotations

import re
from pathlib import Path

from config import settings


def registry_root(*, create: bool = False) -> Path:
    """Return the resolved private registry directory."""
    root = Path(settings.model_registry_dir).expanduser().resolve()
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_artifact_path(artifact_name: str) -> Path:
    """Resolve an artifact name while preventing traversal and symlink escapes."""
    if "/" in artifact_name.replace("\\", "/"):
        raise ValueError("Model artifact names must not contain path separators")
    root = registry_root()
    raw_candidate = root / artifact_name
    if raw_candidate.is_symlink():
        raise ValueError("Model artifact symlinks are not allowed")
    candidate = raw_candidate.resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError("Model artifact is outside the configured registry")
    return candidate


def artifact_name_for(version: str, checksum: str) -> str:
    """Create a stable, filesystem-safe final artifact name."""
    safe_version = re.sub(r"[^A-Za-z0-9._-]+", "-", version).strip(".-")
    safe_version = safe_version[:96] or "model"
    return f"{safe_version}-{checksum[:12]}.keras"
