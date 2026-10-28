"""Baseline training and evaluation."""

from __future__ import annotations

from typing import Any

__all__ = [
    "RegressionMetrics",
    "TrainResult",
    "build_baseline_pipeline",
    "evaluate_regressor",
    "train_baseline",
]


def __getattr__(name: str) -> Any:
    if name in {"RegressionMetrics", "evaluate_regressor"}:
        from modelops.training.evaluate import RegressionMetrics, evaluate_regressor

        return {
            "RegressionMetrics": RegressionMetrics,
            "evaluate_regressor": evaluate_regressor,
        }[name]
    if name == "build_baseline_pipeline":
        from modelops.training.pipeline import build_baseline_pipeline

        return build_baseline_pipeline
    if name in {"TrainResult", "train_baseline"}:
        from modelops.training.train import TrainResult, train_baseline

        return {"TrainResult": TrainResult, "train_baseline": train_baseline}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
