"""End-to-end baseline training for the NYC taxi fare scenario."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from modelops.config import AppConfig, load_config
from modelops.data.features import FEATURE_COLUMNS, TARGET_COLUMN, build_model_frame
from modelops.data.load import load_taxi_parquet
from modelops.data.split import time_based_split
from modelops.data.validate import CleaningReport, validate_and_clean
from modelops.training.evaluate import RegressionMetrics, evaluate_regressor
from modelops.training.pipeline import build_baseline_pipeline

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainResult:
    """Artifacts and metrics from one baseline training run."""

    model_path: Path
    metrics_path: Path
    metrics: RegressionMetrics
    cleaning: dict[str, Any]
    train_rows: int
    test_rows: int
    data_path: str
    dataset_year: int
    dataset_month: int
    max_rows: int
    trained_at_utc: str


def _xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    features = frame.loc[:, list(FEATURE_COLUMNS)]
    target = frame[TARGET_COLUMN]
    return features, target


def train_baseline(
    *,
    data_path: Path | str,
    config: AppConfig | None = None,
    model_output: Path | str | None = None,
    metrics_output: Path | str | None = None,
) -> TrainResult:
    """Load → clean → featurize → time-split → fit LinearRegression → evaluate.

    Persists a joblib Pipeline and a JSON metrics sidecar. Does not promote the
    model to the approved serving path (that is a later lifecycle milestone).
    """
    cfg = config or load_config()
    path = Path(data_path)
    trained_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    raw = load_taxi_parquet(path, max_rows=cfg.max_rows if cfg.max_rows > 0 else None)
    clean, cleaning_report = validate_and_clean(raw)
    if clean.empty:
        raise ValueError("No rows remained after validation; cannot train")

    model_frame = build_model_frame(clean)
    train_frame, test_frame = time_based_split(
        model_frame,
        train_fraction=cfg.train_fraction,
    )

    x_train, y_train = _xy(train_frame)
    x_test, y_test = _xy(test_frame)

    pipeline = build_baseline_pipeline(random_seed=cfg.random_seed)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = evaluate_regressor(y_test.to_numpy(), predictions)

    candidate_dir = cfg.candidate_dir
    candidate_dir.mkdir(parents=True, exist_ok=True)
    model_path = (
        Path(model_output) if model_output else candidate_dir / "baseline_linear_regression.joblib"
    )
    metrics_path = (
        Path(metrics_output)
        if metrics_output
        else candidate_dir / "baseline_linear_regression.metrics.json"
    )
    model_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, model_path)

    payload = {
        "model_type": "sklearn.pipeline.Pipeline[ColumnTransformer, Ridge]",
        "target": TARGET_COLUMN,
        "features": list(FEATURE_COLUMNS),
        "metrics": metrics.as_dict(),
        "cleaning": cleaning_report.as_dict(),
        "train_rows": int(len(train_frame)),
        "test_rows": int(len(test_frame)),
        "data_path": str(path),
        "dataset_year": cfg.year,
        "dataset_month": cfg.month,
        "max_rows": cfg.max_rows,
        "train_fraction": cfg.train_fraction,
        "split_strategy": cfg.split_strategy,
        "random_seed": cfg.random_seed,
        "trained_at_utc": trained_at,
        "scenario": "pre_trip_fare_amount_standard_rate",
    }
    metrics_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Optional processed snapshot for debugging (gitignored).
    processed_dir = cfg.processed_dir
    processed_dir.mkdir(parents=True, exist_ok=True)
    model_frame.to_parquet(processed_dir / "model_frame_latest.parquet", index=False)

    logger.info(
        "Trained baseline mae=%.4f rmse=%.4f r2=%.4f -> %s",
        metrics.mae,
        metrics.rmse,
        metrics.r2,
        model_path,
    )

    return TrainResult(
        model_path=model_path,
        metrics_path=metrics_path,
        metrics=metrics,
        cleaning=cleaning_report.as_dict(),
        train_rows=len(train_frame),
        test_rows=len(test_frame),
        data_path=str(path),
        dataset_year=cfg.year,
        dataset_month=cfg.month,
        max_rows=cfg.max_rows,
        trained_at_utc=trained_at,
    )


def cleaning_report_to_dict(report: CleaningReport) -> dict[str, Any]:
    return report.as_dict()


def train_result_to_dict(result: TrainResult) -> dict[str, Any]:
    data = asdict(result)
    data["model_path"] = str(result.model_path)
    data["metrics_path"] = str(result.metrics_path)
    data["metrics"] = result.metrics.as_dict()
    return data
