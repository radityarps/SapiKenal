"""Pydantic schemas for the SapiKenal mobile backend contract."""

from __future__ import annotations

import json
from enum import Enum
from math import isclose, isfinite
from typing import Any

from pydantic import (  # pyright: ignore[reportMissingImports]
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from config import CANONICAL_LABELS, canonicalize_label

_CANONICAL_SCORE_KEYS = tuple(CANONICAL_LABELS)
_SCORE_TOLERANCE = 0.01


def _canonical_scores(scores: dict[str, float]) -> dict[str, float]:
    """Normalize and validate one complete four-class score object."""
    normalized: dict[str, float] = {}
    for raw_label, raw_score in scores.items():
        label = canonicalize_label(raw_label)
        if label not in _CANONICAL_SCORE_KEYS:
            raise ValueError(f"Unknown model score label: {raw_label}")
        if label in normalized:
            raise ValueError(f"Duplicate model score label: {raw_label}")
        try:
            score = float(raw_score)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid model score for label: {raw_label}") from exc
        if not isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Model scores must be finite and between 0 and 1")
        normalized[label] = score

    if set(normalized) != set(_CANONICAL_SCORE_KEYS):
        raise ValueError("Scores must contain exactly four canonical model classes")
    ordered = {label: normalized[label] for label in _CANONICAL_SCORE_KEYS}
    if not isclose(sum(ordered.values()), 1.0, abs_tol=_SCORE_TOLERANCE):
        raise ValueError("Model scores must sum to one")
    return ordered


class PredictionClass(str, Enum):
    BALI = "bali"
    BRAHMAN = "brahman"
    BRANGUS = "brangus"
    LIMUSIN = "limusin"


class PredictionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_class: PredictionClass
    confidence: float = Field(ge=0.0, le=1.0)
    scores: dict[str, float]

    @model_validator(mode="after")
    def validate_prediction_contract(self) -> PredictionResult:
        scores = _canonical_scores(self.scores)
        top_class = max(scores, key=scores.__getitem__)
        if self.predicted_class.value != top_class:
            raise ValueError("Prediction class must match the highest model score")
        if not isclose(self.confidence, scores[top_class], abs_tol=_SCORE_TOLERANCE):
            raise ValueError("Prediction confidence must match the highest score")
        self.scores = scores
        return self


class ModelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str


class PredictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "success"
    prediction: PredictionResult
    model_info: ModelInfo
    processing_time_ms: int = Field(ge=0)
    preprocessing_time_ms: int = Field(ge=0)
    inference_time_ms: int = Field(ge=0)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "error"
    error_code: str
    message: str = Field(max_length=256)
    model_info: ModelInfo | None = None
    processing_time_ms: int | None = Field(default=None, ge=0)
    preprocessing_time_ms: int | None = Field(default=None, ge=0)
    inference_time_ms: int | None = Field(default=None, ge=0)


class HistoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(min_length=8, max_length=128)
    local_id: int | None = None
    timestamp: int
    predicted_class: PredictionClass
    display_label: str = Field(min_length=1, max_length=128)
    confidence: float = Field(ge=0.0, le=1.0)
    scores: dict[str, float]
    inference_mode: str = Field(min_length=1, max_length=32)
    is_reliable: bool
    processing_ms: int | None = Field(default=None, ge=0)
    title: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    consent_status: str | None = Field(default=None, max_length=32)
    app_version: str | None = Field(default=None, max_length=64)
    model_version: str | None = Field(default=None, max_length=128)
    image_source: str | None = Field(default=None, max_length=32)
    preprocessing_summary: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_source: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def validate_history_contract(self) -> HistoryCreate:
        ordered_scores = _canonical_scores(self.scores)
        top_class = max(ordered_scores, key=ordered_scores.__getitem__)
        if self.predicted_class.value != top_class:
            raise ValueError("Prediction class must match the highest model score")
        if not isclose(
            self.confidence, ordered_scores[top_class], abs_tol=_SCORE_TOLERANCE
        ):
            raise ValueError("Prediction confidence must match the highest score")
        self.scores = ordered_scores
        return self


class HistoryRecord(HistoryCreate):
    id: int
    created_at: int
    updated_at: int

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> HistoryRecord:
        row_data = dict(row)
        if "scores" not in row_data:
            raise ValueError("Stored history scores are missing")
        raw_scores = row_data.pop("scores")
        try:
            scores = (
                json.loads(raw_scores) if isinstance(raw_scores, str) else raw_scores
            )
            if not isinstance(scores, dict):
                raise ValueError("Stored history scores must be an object")
            return cls(**row_data, scores=scores)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError("Invalid stored history scores") from exc


class HistoryListResponse(BaseModel):
    status: str = "success"
    items: list[HistoryRecord]


class HistoryUpsertResponse(BaseModel):
    status: str = "success"
    item: HistoryRecord
