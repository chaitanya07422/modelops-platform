"""Baseline training and evaluation."""

from modelops.training.evaluate import RegressionMetrics, evaluate_regressor
from modelops.training.pipeline import build_baseline_pipeline
from modelops.training.train import TrainResult, train_baseline

__all__ = [
    "RegressionMetrics",
    "TrainResult",
    "build_baseline_pipeline",
    "evaluate_regressor",
    "train_baseline",
]
