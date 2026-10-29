"""Training-time feature reference distributions for PSI drift checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from modelops.data.features import FEATURE_COLUMNS

DEFAULT_N_BINS = 10
REFERENCE_VERSION = 1


def build_feature_reference(
    features: pd.DataFrame,
    *,
    n_bins: int = DEFAULT_N_BINS,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
) -> dict[str, Any]:
    """Build quantile-bin histograms for each numeric feature."""
    missing = [col for col in feature_columns if col not in features.columns]
    if missing:
        raise ValueError(f"Missing feature columns for reference: {missing}")
    if features.empty:
        raise ValueError("Cannot build reference from an empty frame")

    columns: dict[str, Any] = {}
    for col in feature_columns:
        series = pd.to_numeric(features[col], errors="coerce").dropna()
        if series.empty:
            raise ValueError(f"Feature {col} has no finite values for reference")

        # Quantile edges; ensure strictly increasing for histogram binning.
        quantiles = np.linspace(0.0, 1.0, n_bins + 1)
        edges = np.unique(np.quantile(series.to_numpy(dtype=float), quantiles))
        if edges.size < 2:
            # Degenerate constant feature: create a tiny width bin.
            value = float(edges[0]) if edges.size else 0.0
            edges = np.array([value - 0.5, value + 0.5], dtype=float)

        counts, _ = np.histogram(series.to_numpy(dtype=float), bins=edges)
        columns[col] = {
            "bin_edges": [float(x) for x in edges.tolist()],
            "counts": [int(x) for x in counts.tolist()],
            "n": int(series.shape[0]),
            "mean": float(series.mean()),
            "std": float(series.std(ddof=0)),
        }

    return {
        "version": REFERENCE_VERSION,
        "n_bins": n_bins,
        "features": list(feature_columns),
        "n_rows": int(len(features)),
        "columns": columns,
    }


def save_reference(reference: dict[str, Any], path: Path | str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reference, indent=2) + "\n", encoding="utf-8")
    return out


def load_reference(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if "columns" not in payload or "features" not in payload:
        raise ValueError(f"Invalid reference file: {path}")
    return payload
