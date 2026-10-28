"""Pydantic request/response models for the prediction API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from modelops.data.features import FEATURE_COLUMNS, TARGET_COLUMN


class PredictRequest(BaseModel):
    """Pre-trip inputs aligned with the Milestone 1 feature contract."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "passenger_count": 1,
                    "PULocationID": 161,
                    "DOLocationID": 236,
                    "pickup_hour": 8,
                    "pickup_dow": 2,
                    "pickup_day": 15,
                }
            ]
        }
    )

    passenger_count: float = Field(
        ...,
        ge=1,
        le=6,
        description="Number of passengers (1-6), matching training filters.",
    )
    PULocationID: int = Field(..., ge=1, le=265, description="TLC pickup zone ID")
    DOLocationID: int = Field(..., ge=1, le=265, description="TLC drop-off zone ID")
    pickup_hour: int = Field(..., ge=0, le=23, description="Hour of pickup (0-23)")
    pickup_dow: int = Field(
        ...,
        ge=0,
        le=6,
        description="Day of week (Monday=0 … Sunday=6), pandas convention",
    )
    pickup_day: int = Field(..., ge=1, le=31, description="Day of month (1-31)")

    @field_validator("passenger_count")
    @classmethod
    def passenger_must_be_whole_enough(cls, value: float) -> float:
        # Allow 1.0 from JSON numbers; reject clearly fractional counts.
        if abs(value - round(value)) > 1e-6:
            raise ValueError("passenger_count must be a whole number between 1 and 6")
        return float(int(round(value)))

    def as_feature_frame_dict(self) -> dict[str, Any]:
        """Ordered feature mapping for pandas DataFrame construction."""
        payload = self.model_dump()
        return {name: payload[name] for name in FEATURE_COLUMNS}


class PredictResponse(BaseModel):
    prediction: float = Field(..., description="Predicted metered fare_amount in USD")
    target: str = TARGET_COLUMN
    currency: str = "USD"
    model_id: str | None = None
    disclaimer: str = "Learning/demo estimate only — not an official NYC TLC fare quote."


class HealthResponse(BaseModel):
    status: str = "ok"


class ReadyResponse(BaseModel):
    status: str
    model_loaded: bool
    detail: str | None = None


class ModelInfoResponse(BaseModel):
    ready: bool
    model_path: str | None = None
    model_type: str | None = None
    target: str | None = TARGET_COLUMN
    features: list[str] = Field(default_factory=lambda: list(FEATURE_COLUMNS))
    scenario: str | None = None
    trained_at_utc: str | None = None
    dataset_year: int | None = None
    dataset_month: int | None = None
    metrics: dict[str, float | int] | None = None
    detail: str | None = None


class ErrorResponse(BaseModel):
    detail: str
