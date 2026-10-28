"""Quality gates, promotion, rollback, and MLflow logging tests."""

from __future__ import annotations

import json
from pathlib import Path

from modelops.config import AppConfig, load_config
from modelops.lifecycle.gates import QualityThresholds, evaluate_quality_gates
from modelops.lifecycle.promote import promote_candidate, rollback_approved
from modelops.training.evaluate import RegressionMetrics
from modelops.training.train import train_baseline

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "synthetic_yellow_trips.parquet"


def _config_for_tmp(tmp_path: Path, *, tracking: Path) -> AppConfig:
    base = load_config(repo_root=REPO)
    return AppConfig(
        project_name=base.project_name,
        environment="test",
        year=base.year,
        month=base.month,
        max_rows=base.max_rows,
        raw_dir=base.raw_dir,
        processed_dir=tmp_path / "processed",
        fixtures_dir=base.fixtures_dir,
        random_seed=base.random_seed,
        split_strategy=base.split_strategy,
        train_fraction=base.train_fraction,
        approved_model_path=tmp_path / "approved" / "model.joblib",
        candidate_dir=tmp_path / "candidates",
        data_url=None,
        mlflow_tracking_uri=f"file:{tracking.resolve()}",
        mlflow_experiment_name="modelops-test",
        mlflow_registered_model_name="modelops-test",
        max_mae=20.0,
        max_rmse=30.0,
        min_r2=-1.0,  # synthetic fixture can have weak R²
    )


def test_quality_gate_pass_and_fail() -> None:
    metrics = RegressionMetrics(mae=5.0, rmse=8.0, r2=0.5, n_samples=100)
    thresholds = QualityThresholds(max_mae=10.0, max_rmse=15.0, min_r2=0.3)
    assert evaluate_quality_gates(metrics, thresholds).passed is True

    bad = RegressionMetrics(mae=12.0, rmse=8.0, r2=0.5, n_samples=100)
    result = evaluate_quality_gates(bad, thresholds)
    assert result.passed is False
    assert any("mae" in f for f in result.failures)


def test_quality_gate_require_improvement() -> None:
    candidate = RegressionMetrics(mae=6.0, rmse=8.0, r2=0.5, n_samples=100)
    approved = RegressionMetrics(mae=5.0, rmse=7.0, r2=0.6, n_samples=100)
    thresholds = QualityThresholds(max_mae=10.0, max_rmse=15.0, min_r2=0.3)
    result = evaluate_quality_gates(
        candidate,
        thresholds,
        approved_metrics=approved,
        require_improvement=True,
    )
    assert result.passed is False
    assert result.compared_to_approved is True


def test_train_logs_mlflow_and_promote_rollback(tmp_path: Path) -> None:
    tracking = tmp_path / "mlruns"
    config = _config_for_tmp(tmp_path, tracking=tracking)
    result = train_baseline(
        data_path=FIXTURE,
        config=config,
        log_mlflow=True,
        register_model=False,
    )
    assert result.model_path.exists()
    assert result.mlflow_run_id
    assert result.gate is not None
    assert result.gate.passed is True

    payload = json.loads(result.metrics_path.read_text(encoding="utf-8"))
    assert payload["mlflow_run_id"] == result.mlflow_run_id

    promoted = promote_candidate(
        candidate_model=result.model_path,
        candidate_metrics=result.metrics_path,
        config=config,
    )
    assert promoted.promoted is True
    assert config.approved_model_path.exists()
    assert config.approved_metrics_path.exists()

    # Second promotion archives the first approved model.
    result2 = train_baseline(
        data_path=FIXTURE,
        config=config,
        model_output=config.candidate_dir / "v2.joblib",
        metrics_output=config.candidate_dir / "v2.metrics.json",
        log_mlflow=True,
    )
    promoted2 = promote_candidate(
        candidate_model=result2.model_path,
        candidate_metrics=result2.metrics_path,
        config=config,
    )
    assert promoted2.promoted is True
    assert promoted2.history_dir is not None
    assert (promoted2.history_dir / "model.joblib").exists()

    rolled = rollback_approved(config=config)
    assert config.approved_model_path.exists()
    assert "restored_from" in rolled


def test_promote_blocked_when_gate_fails(tmp_path: Path) -> None:
    tracking = tmp_path / "mlruns"
    config = _config_for_tmp(tmp_path, tracking=tracking)
    # Unreachable thresholds for synthetic/demo metrics.
    strict = AppConfig(
        **{
            **config.__dict__,
            "max_mae": 0.0001,
            "max_rmse": 0.0001,
            "min_r2": 0.9999,
        }
    )
    result = train_baseline(data_path=FIXTURE, config=strict, log_mlflow=False)
    assert result.gate is not None
    assert result.gate.passed is False

    promoted = promote_candidate(
        candidate_model=result.model_path,
        candidate_metrics=result.metrics_path,
        config=strict,
    )
    assert promoted.promoted is False
    assert promoted.message == "quality_gate_failed"
    assert not strict.approved_model_path.exists()
