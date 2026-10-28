"""Promote candidates to approved and roll back to prior approved snapshots.

Filesystem promotion keeps the learning path simple and interview-explainable.
MLflow still records the training run; the approved pointer is a local path the
API loads (Milestone 2). Registry aliases can wrap this later if needed.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelops.config import AppConfig, load_config
from modelops.lifecycle.gates import (
    GateResult,
    QualityThresholds,
    evaluate_quality_gates,
)
from modelops.training.evaluate import RegressionMetrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PromoteResult:
    promoted: bool
    approved_model_path: Path
    approved_metrics_path: Path
    history_dir: Path | None
    gate: GateResult
    message: str
    mlflow_run_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["approved_model_path"] = str(self.approved_model_path)
        data["approved_metrics_path"] = str(self.approved_metrics_path)
        data["history_dir"] = str(self.history_dir) if self.history_dir else None
        data["gate"] = self.gate.as_dict()
        return data


class PromotionError(RuntimeError):
    """Raised when promotion cannot proceed (missing files, gate failure)."""


def _load_metrics_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _metrics_from_payload(payload: dict[str, Any]) -> RegressionMetrics:
    raw = payload["metrics"]
    return RegressionMetrics(
        mae=float(raw["mae"]),
        rmse=float(raw["rmse"]),
        r2=float(raw["r2"]),
        n_samples=int(raw["n_samples"]),
    )


def _approved_sidecar(approved_model: Path) -> Path:
    return approved_model.parent / "model.metrics.json"


def _history_root(approved_model: Path) -> Path:
    return approved_model.parent / "history"


def promote_candidate(
    *,
    candidate_model: Path | str | None = None,
    candidate_metrics: Path | str | None = None,
    config: AppConfig | None = None,
    require_improvement: bool = False,
    force: bool = False,
) -> PromoteResult:
    """Copy a gated candidate into the approved serving path.

    Previous approved artifacts (if any) are moved under ``models/approved/history/``.
    """
    cfg = config or load_config()
    model_src = (
        Path(candidate_model)
        if candidate_model
        else (cfg.candidate_dir / "baseline_linear_regression.joblib")
    )
    metrics_src = (
        Path(candidate_metrics)
        if candidate_metrics
        else (cfg.candidate_dir / "baseline_linear_regression.metrics.json")
    )
    approved = cfg.approved_model_path
    approved_metrics = _approved_sidecar(approved)

    if not model_src.exists():
        raise PromotionError(f"Candidate model missing: {model_src}")
    if not metrics_src.exists():
        raise PromotionError(f"Candidate metrics missing: {metrics_src}")

    payload = _load_metrics_file(metrics_src)
    metrics = _metrics_from_payload(payload)
    thresholds = QualityThresholds(
        max_mae=cfg.max_mae,
        max_rmse=cfg.max_rmse,
        min_r2=cfg.min_r2,
    )

    approved_metrics_obj: RegressionMetrics | None = None
    if approved_metrics.exists():
        try:
            approved_metrics_obj = _metrics_from_payload(_load_metrics_file(approved_metrics))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            logger.warning("Could not parse existing approved metrics at %s", approved_metrics)

    gate = evaluate_quality_gates(
        metrics,
        thresholds,
        approved_metrics=approved_metrics_obj,
        require_improvement=require_improvement,
    )
    if not gate.passed and not force:
        return PromoteResult(
            promoted=False,
            approved_model_path=approved,
            approved_metrics_path=approved_metrics,
            history_dir=None,
            gate=gate,
            message="quality_gate_failed",
            mlflow_run_id=payload.get("mlflow_run_id"),
        )

    history_dir: Path | None = None
    approved.parent.mkdir(parents=True, exist_ok=True)
    if approved.exists():
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        history_dir = _history_root(approved) / stamp
        history_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(approved, history_dir / "model.joblib")
        if approved_metrics.exists():
            shutil.copy2(approved_metrics, history_dir / "model.metrics.json")
        logger.info("Archived previous approved model to %s", history_dir)

    shutil.copy2(model_src, approved)
    promote_payload = dict(payload)
    promote_payload["promoted_at_utc"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    promote_payload["promoted_from"] = str(model_src)
    promote_payload["gate"] = gate.as_dict()
    promote_payload["forced"] = force and not gate.passed
    approved_metrics.write_text(json.dumps(promote_payload, indent=2) + "\n", encoding="utf-8")

    pointer = approved.parent / "CURRENT.json"
    pointer.write_text(
        json.dumps(
            {
                "approved_model": approved.name,
                "metrics_file": approved_metrics.name,
                "promoted_at_utc": promote_payload["promoted_at_utc"],
                "mlflow_run_id": payload.get("mlflow_run_id"),
                "metrics": metrics.as_dict(),
                "history_dir": str(history_dir) if history_dir else None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    logger.info("Promoted candidate %s -> %s", model_src, approved)
    return PromoteResult(
        promoted=True,
        approved_model_path=approved,
        approved_metrics_path=approved_metrics,
        history_dir=history_dir,
        gate=gate,
        message="promoted" if gate.passed else "promoted_forced",
        mlflow_run_id=payload.get("mlflow_run_id"),
    )


def rollback_approved(*, config: AppConfig | None = None) -> dict[str, Any]:
    """Restore the most recent history snapshot as the approved model."""
    cfg = config or load_config()
    approved = cfg.approved_model_path
    history_root = _history_root(approved)
    if not history_root.exists():
        raise PromotionError(f"No history directory at {history_root}")

    snapshots = sorted([p for p in history_root.iterdir() if p.is_dir()], reverse=True)
    if not snapshots:
        raise PromotionError(f"No snapshots under {history_root}")

    latest = snapshots[0]
    model_src = latest / "model.joblib"
    metrics_src = latest / "model.metrics.json"
    if not model_src.exists():
        raise PromotionError(f"Snapshot missing model: {model_src}")

    # Archive current approved before overwrite (optional safety).
    if approved.exists():
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        outgoing = history_root / f"pre_rollback_{stamp}"
        outgoing.mkdir(parents=True, exist_ok=True)
        shutil.copy2(approved, outgoing / "model.joblib")
        sidecar = _approved_sidecar(approved)
        if sidecar.exists():
            shutil.copy2(sidecar, outgoing / "model.metrics.json")

    shutil.copy2(model_src, approved)
    approved_metrics = _approved_sidecar(approved)
    if metrics_src.exists():
        shutil.copy2(metrics_src, approved_metrics)

    payload = {
        "rolled_back_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "restored_from": str(latest),
        "approved_model_path": str(approved),
    }
    (approved.parent / "CURRENT.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    logger.info("Rolled back approved model from %s", latest)
    return payload
