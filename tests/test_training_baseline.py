"""Baseline training tests using the synthetic fixture only (no network)."""

from __future__ import annotations

from pathlib import Path

import joblib
import pytest
from sklearn.pipeline import Pipeline

from modelops.config import load_config
from modelops.data.features import FEATURE_COLUMNS
from modelops.training.evaluate import evaluate_regressor
from modelops.training.pipeline import build_baseline_pipeline
from modelops.training.train import train_baseline

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "synthetic_yellow_trips.parquet"


def test_evaluate_regressor_metrics() -> None:
    metrics = evaluate_regressor([1.0, 2.0, 3.0], [1.0, 2.0, 4.0])
    assert metrics.n_samples == 3
    assert metrics.mae == pytest.approx(1.0 / 3.0)
    assert metrics.rmse == pytest.approx((1.0 / 3.0) ** 0.5)
    assert metrics.r2 < 1.0


def test_baseline_pipeline_feature_contract() -> None:
    pipe = build_baseline_pipeline(random_seed=42)
    assert isinstance(pipe, Pipeline)
    assert pipe.named_steps["model"].__class__.__name__ == "Ridge"


def test_train_baseline_on_fixture(tmp_path: Path) -> None:
    config = load_config(repo_root=REPO)
    model_out = tmp_path / "model.joblib"
    metrics_out = tmp_path / "metrics.json"

    result = train_baseline(
        data_path=FIXTURE,
        config=config,
        model_output=model_out,
        metrics_output=metrics_out,
        log_mlflow=False,
    )

    assert model_out.exists()
    assert metrics_out.exists()
    assert result.train_rows > 0
    assert result.test_rows > 0
    assert result.metrics.n_samples == result.test_rows
    assert result.metrics.mae >= 0.0
    assert result.metrics.rmse >= result.metrics.mae
    # R² can be negative when the model underperforms the mean baseline.
    assert result.metrics.r2 == result.metrics.r2  # not NaN
    assert abs(result.metrics.r2) < 1e6

    loaded = joblib.load(model_out)
    assert isinstance(loaded, Pipeline)
    # Smoke predict with one row shaped like features.
    import pandas as pd

    sample = pd.DataFrame(
        [
            {
                "passenger_count": 1.0,
                "PULocationID": 10,
                "DOLocationID": 20,
                "pickup_hour": 8,
                "pickup_dow": 2,
                "pickup_day": 5,
            }
        ]
    )
    pred = loaded.predict(sample[list(FEATURE_COLUMNS)])
    assert pred.shape == (1,)
