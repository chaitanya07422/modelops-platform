"""Load and score the approved sklearn Pipeline once per process.

Training never runs here. Prediction failures raise typed errors that routes
map to HTTP statuses without leaking stack traces or filesystem secrets.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from modelops.data.features import FEATURE_COLUMNS, TARGET_COLUMN

logger = logging.getLogger(__name__)


class ModelNotReadyError(RuntimeError):
    """Raised when a prediction is requested before a valid model is loaded."""


class ModelLoadError(RuntimeError):
    """Raised when the configured artifact is missing or invalid."""


@dataclass
class ModelService:
    """In-memory holder for the serving pipeline and safe metadata."""

    model_path: Path | None = None
    pipeline: Pipeline | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    load_error: str | None = None

    @property
    def ready(self) -> bool:
        return self.pipeline is not None and self.load_error is None

    def load(self, model_path: Path, *, metrics_path: Path | None = None) -> None:
        """Load a joblib Pipeline from disk; record a clear error on failure."""
        self.model_path = Path(model_path)
        self.pipeline = None
        self.metadata = {}
        self.load_error = None

        if not self.model_path.exists():
            self.load_error = "model_artifact_missing"
            logger.error("Model artifact not found at %s", self.model_path)
            raise ModelLoadError(f"Model artifact not found at {self.model_path}")

        try:
            loaded = joblib.load(self.model_path)
        except Exception as exc:  # noqa: BLE001 - boundary: corrupt artifact
            self.load_error = "model_artifact_invalid"
            logger.exception("Failed to load model from %s", self.model_path)
            raise ModelLoadError("Model artifact could not be loaded") from exc

        if not isinstance(loaded, Pipeline):
            self.load_error = "model_artifact_invalid"
            raise ModelLoadError("Model artifact is not a sklearn Pipeline")

        self.pipeline = loaded
        self.metadata = self._load_metadata(metrics_path)
        logger.info("Loaded model from %s", self.model_path)

    def _load_metadata(self, metrics_path: Path | None) -> dict[str, Any]:
        # Convention from training: foo.joblib -> foo.metrics.json
        path = metrics_path
        if path is None and self.model_path is not None:
            path = self.model_path.parent / f"{self.model_path.stem}.metrics.json"

        if path is None or not path.exists():
            model_step = None
            if self.pipeline is not None:
                model_step = self.pipeline.named_steps.get("model", self.pipeline)
            return {
                "target": TARGET_COLUMN,
                "features": list(FEATURE_COLUMNS),
                "model_type": type(model_step).__name__ if model_step is not None else None,
            }

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Could not parse metrics sidecar at %s", path)
            return {"target": TARGET_COLUMN, "features": list(FEATURE_COLUMNS)}

        safe_keys = (
            "model_type",
            "target",
            "features",
            "metrics",
            "scenario",
            "trained_at_utc",
            "dataset_year",
            "dataset_month",
            "train_rows",
            "test_rows",
            "max_rows",
            "split_strategy",
        )
        return {key: payload[key] for key in safe_keys if key in payload}

    def predict_one(self, features: dict[str, Any]) -> float:
        if not self.ready or self.pipeline is None:
            raise ModelNotReadyError("Model is not ready")

        frame = pd.DataFrame([features], columns=list(FEATURE_COLUMNS))
        prediction = self.pipeline.predict(frame)
        value = float(prediction[0])
        if value != value:  # NaN
            raise RuntimeError("Model returned a non-finite prediction")
        return value

    def info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "ready": self.ready,
            "model_path": str(self.model_path) if self.model_path else None,
            "target": self.metadata.get("target", TARGET_COLUMN),
            "features": self.metadata.get("features", list(FEATURE_COLUMNS)),
            "model_type": self.metadata.get("model_type"),
            "scenario": self.metadata.get("scenario"),
            "trained_at_utc": self.metadata.get("trained_at_utc"),
            "dataset_year": self.metadata.get("dataset_year"),
            "dataset_month": self.metadata.get("dataset_month"),
            "metrics": self.metadata.get("metrics"),
            "detail": None if self.ready else (self.load_error or "model_not_loaded"),
        }
        return info
