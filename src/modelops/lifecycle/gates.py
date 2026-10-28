"""Configurable model-quality gates for promotion decisions.

A successful training run is not enough — candidates must pass absolute metric
thresholds (and optionally beat the current approved model) before promotion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from modelops.training.evaluate import RegressionMetrics


@dataclass(frozen=True)
class QualityThresholds:
    max_mae: float
    max_rmse: float
    min_r2: float


@dataclass(frozen=True)
class GateResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    metrics: dict[str, float | int] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    compared_to_approved: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_quality_gates(
    metrics: RegressionMetrics,
    thresholds: QualityThresholds,
    *,
    approved_metrics: RegressionMetrics | None = None,
    require_improvement: bool = False,
) -> GateResult:
    """Evaluate absolute thresholds and optional improvement vs approved.

    Parameters
    ----------
    require_improvement:
        When True and ``approved_metrics`` is provided, the candidate must have
        MAE less than or equal to the approved model's MAE (no regression).
    """
    failures: list[str] = []
    if metrics.mae > thresholds.max_mae:
        failures.append(f"mae {metrics.mae:.4f} exceeds max_mae {thresholds.max_mae:.4f}")
    if metrics.rmse > thresholds.max_rmse:
        failures.append(f"rmse {metrics.rmse:.4f} exceeds max_rmse {thresholds.max_rmse:.4f}")
    if metrics.r2 < thresholds.min_r2:
        failures.append(f"r2 {metrics.r2:.4f} below min_r2 {thresholds.min_r2:.4f}")

    compared = False
    if require_improvement and approved_metrics is not None:
        compared = True
        if metrics.mae > approved_metrics.mae:
            failures.append(
                f"mae {metrics.mae:.4f} worse than approved mae {approved_metrics.mae:.4f}"
            )

    return GateResult(
        passed=len(failures) == 0,
        failures=failures,
        metrics=metrics.as_dict(),
        thresholds={
            "max_mae": thresholds.max_mae,
            "max_rmse": thresholds.max_rmse,
            "min_r2": thresholds.min_r2,
        },
        compared_to_approved=compared,
    )
