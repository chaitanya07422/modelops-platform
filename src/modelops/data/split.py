"""Train / evaluation splits for temporal trip data."""

from __future__ import annotations

import pandas as pd


def time_based_split(
    frame: pd.DataFrame,
    *,
    time_column: str = "tpep_pickup_datetime",
    train_fraction: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split chronologically by pickup time.

    Earlier trips train the model; later trips evaluate it. This matches a
    deploy-forward mindset better than a random shuffle on time-ordered events.
    """
    if not 0.0 < train_fraction < 1.0:
        raise ValueError(f"train_fraction must be in (0, 1); got {train_fraction}")
    if time_column not in frame.columns:
        raise ValueError(f"Missing time column {time_column!r}")
    if frame.empty:
        raise ValueError("Cannot split an empty frame")

    ordered = frame.sort_values(time_column, kind="mergesort").reset_index(drop=True)
    cut = int(len(ordered) * train_fraction)
    if cut <= 0 or cut >= len(ordered):
        raise ValueError(
            f"Split produced empty train or test set (n={len(ordered)}, "
            f"train_fraction={train_fraction})"
        )
    train = ordered.iloc[:cut].copy()
    test = ordered.iloc[cut:].copy()
    return train, test
