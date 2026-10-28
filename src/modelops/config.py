"""Load and resolve ModelOps configuration.

Combines ``configs/default.yaml`` with environment-variable overrides so local
runs stay reproducible without baking secrets into code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "default.yaml"

# Official TLC yellow taxi Parquet hosting (CloudFront CDN used by nyc.gov links).
TLC_YELLOW_PARQUET_URL_TEMPLATE = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year:04d}-{month:02d}.parquet"
)


@dataclass(frozen=True)
class AppConfig:
    """Resolved runtime configuration for data, training, tracking, and gates."""

    project_name: str
    environment: str
    year: int
    month: int
    max_rows: int
    raw_dir: Path
    processed_dir: Path
    fixtures_dir: Path
    random_seed: int
    split_strategy: str
    train_fraction: float
    approved_model_path: Path
    candidate_dir: Path
    data_url: str | None
    mlflow_tracking_uri: str
    mlflow_experiment_name: str
    mlflow_registered_model_name: str
    max_mae: float
    max_rmse: float
    min_r2: float

    @property
    def raw_parquet_path(self) -> Path:
        return self.raw_dir / f"yellow_tripdata_{self.year:04d}-{self.month:02d}.parquet"

    @property
    def resolved_data_url(self) -> str:
        if self.data_url:
            return self.data_url
        return TLC_YELLOW_PARQUET_URL_TEMPLATE.format(year=self.year, month=self.month)

    @property
    def approved_metrics_path(self) -> Path:
        return self.approved_model_path.parent / "model.metrics.json"


def _as_path(value: str | Path, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def load_config(config_path: Path | None = None, repo_root: Path | None = None) -> AppConfig:
    """Load YAML defaults and apply ``MODELOPS_*`` / ``MLFLOW_*`` env overrides."""
    root = repo_root or REPO_ROOT
    path = config_path or DEFAULT_CONFIG_PATH
    with path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}

    data = raw.get("data", {})
    training = raw.get("training", {})
    model = raw.get("model", {})
    project = raw.get("project", {})
    mlflow_cfg = raw.get("mlflow", {})
    gates = raw.get("quality_gates", {})

    year = _env_int("MODELOPS_TAXI_YEAR", int(data.get("year", 2024)))
    month = _env_int("MODELOPS_TAXI_MONTH", int(data.get("month", 1)))
    max_rows = _env_int("MODELOPS_MAX_ROWS", int(data.get("max_rows", 50_000)))
    data_url = os.getenv("MODELOPS_TAXI_DATA_URL") or None

    # Approved path is the promotion target — do not overload with API override.
    approved = _as_path(
        os.getenv("MODELOPS_APPROVED_MODEL_PATH")
        or model.get("approved_path", "models/approved/model.joblib"),
        root,
    )

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI") or str(
        mlflow_cfg.get("tracking_uri", "file:./mlruns")
    )
    if tracking_uri.startswith("file:") and not tracking_uri.startswith("file:/"):
        # Resolve relative file URIs against the repo root.
        relative = tracking_uri.removeprefix("file:")
        tracking_uri = f"file:{(_as_path(relative, root)).resolve()}"

    return AppConfig(
        project_name=str(project.get("name", "modelops")),
        environment=os.getenv("MODELOPS_ENV", str(project.get("environment", "development"))),
        year=year,
        month=month,
        max_rows=max_rows,
        raw_dir=_as_path(data.get("raw_dir", "data/raw"), root),
        processed_dir=_as_path(data.get("processed_dir", "data/processed"), root),
        fixtures_dir=_as_path(data.get("fixtures_dir", "data/fixtures"), root),
        random_seed=_env_int("MODELOPS_RANDOM_SEED", int(training.get("random_seed", 42))),
        split_strategy=str(training.get("split_strategy", "time_based")),
        train_fraction=_env_float(
            "MODELOPS_TRAIN_FRACTION",
            float(training.get("train_fraction", 0.8)),
        ),
        approved_model_path=approved,
        candidate_dir=_as_path(model.get("candidate_dir", "models/candidates"), root),
        data_url=data_url,
        mlflow_tracking_uri=tracking_uri,
        mlflow_experiment_name=os.getenv("MLFLOW_EXPERIMENT_NAME")
        or str(mlflow_cfg.get("experiment_name", "modelops-taxi-fare")),
        mlflow_registered_model_name=os.getenv("MLFLOW_REGISTERED_MODEL_NAME")
        or str(mlflow_cfg.get("registered_model_name", "modelops-taxi-fare")),
        max_mae=_env_float("MODELOPS_MAX_MAE", float(gates.get("max_mae", 10.0))),
        max_rmse=_env_float("MODELOPS_MAX_RMSE", float(gates.get("max_rmse", 15.0))),
        min_r2=_env_float("MODELOPS_MIN_R2", float(gates.get("min_r2", 0.3))),
    )
