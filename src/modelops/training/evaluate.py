"""Regression metrics for fare_amount evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


@dataclass(frozen=True)
class RegressionMetrics:
    """Held-out regression scores in units of the target (USD for fare_amount)."""

    mae: float
    rmse: float
    r2: float
    n_samples: int

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def evaluate_regressor(
    y_true: np.ndarray | list[float],
    y_pred: np.ndarray | list[float],
) -> RegressionMetrics:
    """Compute MAE, RMSE, and R² on a held-out set."""
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)
    if y_true_arr.shape != y_pred_arr.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    if y_true_arr.size == 0:
        raise ValueError("Cannot evaluate on an empty prediction set")

    mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
    rmse = float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr)))
    r2 = float(r2_score(y_true_arr, y_pred_arr))
    return RegressionMetrics(mae=mae, rmse=rmse, r2=r2, n_samples=int(y_true_arr.size))
