"""MLflow experiment setup and training-run logging."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient

from modelops.config import AppConfig
from modelops.training.evaluate import RegressionMetrics

logger = logging.getLogger(__name__)


def setup_mlflow(config: AppConfig) -> str:
    """Configure tracking URI and ensure the experiment exists.

    Returns the experiment name.
    """
    tracking_uri = config.mlflow_tracking_uri
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(config.mlflow_experiment_name)
    logger.info(
        "MLflow tracking_uri=%s experiment=%s",
        tracking_uri,
        config.mlflow_experiment_name,
    )
    return config.mlflow_experiment_name


def log_training_run(
    *,
    config: AppConfig,
    metrics: RegressionMetrics,
    params: dict[str, Any],
    tags: dict[str, str] | None = None,
    model_path: Path,
    metrics_path: Path,
    pipeline: Any | None = None,
    register_model: bool = False,
) -> str:
    """Start a run, log params/metrics/artifacts, optionally register the model.

    Returns
    -------
    str
        MLflow run id.
    """
    setup_mlflow(config)
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        for key, value in params.items():
            if value is None:
                continue
            mlflow.log_param(key, value)

        mlflow.log_metric("mae", metrics.mae)
        mlflow.log_metric("rmse", metrics.rmse)
        mlflow.log_metric("r2", metrics.r2)
        mlflow.log_metric("n_samples", float(metrics.n_samples))

        for key, value in (tags or {}).items():
            mlflow.set_tag(key, value)

        mlflow.log_artifact(str(model_path))
        mlflow.log_artifact(str(metrics_path))

        if pipeline is not None:
            # Log sklearn flavor for UI compare / later registry use.
            mlflow.sklearn.log_model(
                sk_model=pipeline,
                artifact_path="sklearn_model",
                registered_model_name=(
                    config.mlflow_registered_model_name if register_model else None
                ),
            )

        logger.info("Logged MLflow run_id=%s", run_id)
        return run_id


def list_recent_runs(config: AppConfig, *, max_results: int = 10) -> list[dict[str, Any]]:
    """Return recent runs for comparison (params + key metrics)."""
    setup_mlflow(config)
    client = MlflowClient()
    experiment = client.get_experiment_by_name(config.mlflow_experiment_name)
    if experiment is None:
        return []
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attributes.start_time DESC"],
        max_results=max_results,
    )
    rows: list[dict[str, Any]] = []
    for run in runs:
        rows.append(
            {
                "run_id": run.info.run_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "params": dict(run.data.params),
                "metrics": dict(run.data.metrics),
                "tags": dict(run.data.tags),
            }
        )
    return rows
