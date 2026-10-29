"""Milestone 9: batch scoring, PSI drift, delayed ground-truth quality."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from modelops.api.model_service import ModelService
from modelops.batch.score import score_batch
from modelops.data.features import FEATURE_COLUMNS, TARGET_COLUMN
from modelops.monitoring.drift import compute_drift_report, run_drift_check
from modelops.monitoring.quality import compute_quality_report, run_quality_check
from modelops.monitoring.reference import build_feature_reference, save_reference
from modelops.training.evaluate import evaluate_regressor
from modelops.training.pipeline import build_baseline_pipeline


def _tiny_frame(n: int = 40, *, shift: float = 0.0) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "passenger_count": rng.integers(1, 5, size=n).astype(float),
            "PULocationID": rng.integers(1, 50, size=n),
            "DOLocationID": rng.integers(1, 50, size=n),
            "pickup_hour": rng.integers(0, 24, size=n),
            "pickup_dow": rng.integers(0, 7, size=n),
            "pickup_day": rng.integers(1, 29, size=n),
            TARGET_COLUMN: 8.0 + rng.normal(0, 1.0, size=n) + shift,
        }
    )


@pytest.fixture()
def trained_model(tmp_path: Path) -> tuple[Path, Path, pd.DataFrame]:
    train = _tiny_frame(80)
    x = train.loc[:, list(FEATURE_COLUMNS)]
    y = train[TARGET_COLUMN]
    pipe = build_baseline_pipeline(random_seed=0)
    pipe.fit(x, y)
    model_path = tmp_path / "model.joblib"
    import joblib

    joblib.dump(pipe, model_path)
    metrics_path = tmp_path / "model.metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "model_type": "Ridge",
                "target": TARGET_COLUMN,
                "features": list(FEATURE_COLUMNS),
                "metrics": {"mae": 1.0, "rmse": 1.2, "r2": 0.5, "n_samples": 20},
            }
        ),
        encoding="utf-8",
    )
    ref = build_feature_reference(x)
    save_reference(ref, tmp_path / "reference_features.json")
    return model_path, metrics_path, train


def test_predict_frame_and_batch_score(
    tmp_path: Path, trained_model: tuple[Path, Path, pd.DataFrame]
):
    model_path, metrics_path, train = trained_model
    service = ModelService()
    service.load(model_path, metrics_path=metrics_path)
    preds = service.predict_frame(train)
    assert len(preds) == len(train)

    input_path = tmp_path / "batch_in.parquet"
    output_path = tmp_path / "batch_out.parquet"
    train.to_parquet(input_path, index=False)
    summary = score_batch(
        input_path=input_path,
        output_path=output_path,
        model_path=model_path,
        metrics_path=metrics_path,
    )
    assert summary["n_rows"] == len(train)
    scored = pd.read_parquet(output_path)
    assert "prediction" in scored.columns
    assert len(scored) == len(train)


def test_drift_identical_vs_shifted(tmp_path: Path, trained_model: tuple[Path, Path, pd.DataFrame]):
    _model_path, _metrics_path, train = trained_model
    reference = build_feature_reference(train.loc[:, list(FEATURE_COLUMNS)])
    ref_path = tmp_path / "reference_features.json"
    save_reference(reference, ref_path)

    same = compute_drift_report(train, reference, psi_threshold=0.25)
    assert same["any_above_threshold"] is False
    assert same["max_psi"] is not None
    assert same["max_psi"] < 0.25

    shifted = train.copy()
    shifted["passenger_count"] = shifted["passenger_count"] + 20.0
    drifted = compute_drift_report(shifted, reference, psi_threshold=0.1)
    assert drifted["any_above_threshold"] is True
    assert "passenger_count" in drifted["breached_features"]

    in_path = tmp_path / "shifted.parquet"
    shifted.to_parquet(in_path, index=False)
    report = run_drift_check(
        input_path=in_path,
        reference_path=ref_path,
        report_path=tmp_path / "drift_report.json",
        psi_threshold=0.1,
    )
    assert report["any_above_threshold"] is True
    assert (tmp_path / "drift_report.json").exists()


def test_quality_matches_evaluate_regressor(
    tmp_path: Path, trained_model: tuple[Path, Path, pd.DataFrame]
):
    model_path, metrics_path, train = trained_model
    service = ModelService()
    service.load(model_path, metrics_path=metrics_path)
    preds = service.predict_frame(train)
    frame = train.copy()
    frame["prediction"] = preds.to_numpy()

    expected = evaluate_regressor(
        frame[TARGET_COLUMN].to_numpy(),
        frame["prediction"].to_numpy(),
    )
    report = compute_quality_report(frame)
    assert report["metrics"]["mae"] == pytest.approx(expected.mae)
    assert report["metrics"]["rmse"] == pytest.approx(expected.rmse)
    assert report["metrics"]["r2"] == pytest.approx(expected.r2)

    path = tmp_path / "scored.parquet"
    frame.to_parquet(path, index=False)
    written = run_quality_check(predictions_path=path, report_path=tmp_path / "quality.json")
    assert written["n_labeled"] == len(frame)
    assert (tmp_path / "quality.json").exists()
