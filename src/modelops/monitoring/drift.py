"""Population Stability Index (PSI) drift checks vs a training reference."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from modelops.data.features import FEATURE_COLUMNS
from modelops.monitoring.reference import load_reference

logger = logging.getLogger(__name__)

# Common rule of thumb: PSI < 0.1 stable; 0.1–0.25 moderate; > 0.25 major shift.
DEFAULT_PSI_THRESHOLD = 0.25
_EPS = 1e-6


def _psi(expected: np.ndarray, actual: np.ndarray) -> float:
    exp = np.asarray(expected, dtype=float)
    act = np.asarray(actual, dtype=float)
    exp = np.clip(exp, _EPS, None)
    act = np.clip(act, _EPS, None)
    exp = exp / exp.sum()
    act = act / act.sum()
    return float(np.sum((act - exp) * np.log(act / exp)))


def compute_feature_psi(
    values: pd.Series,
    *,
    bin_edges: list[float],
    reference_counts: list[int],
) -> float:
    edges = np.asarray(bin_edges, dtype=float)
    series = pd.to_numeric(values, errors="coerce").dropna()
    if series.empty:
        return float("inf")
    counts, _ = np.histogram(series.to_numpy(dtype=float), bins=edges)
    return _psi(np.asarray(reference_counts, dtype=float), counts.astype(float))


def compute_drift_report(
    features: pd.DataFrame,
    reference: dict[str, Any],
    *,
    psi_threshold: float = DEFAULT_PSI_THRESHOLD,
) -> dict[str, Any]:
    """Compare batch features to reference histograms; flag PSI breaches."""
    per_feature: dict[str, Any] = {}
    breached: list[str] = []
    for col in reference.get("features", list(FEATURE_COLUMNS)):
        col_ref = reference["columns"].get(col)
        if col_ref is None:
            continue
        if col not in features.columns:
            per_feature[col] = {"psi": None, "error": "missing_column", "breached": True}
            breached.append(col)
            continue
        psi = compute_feature_psi(
            features[col],
            bin_edges=col_ref["bin_edges"],
            reference_counts=col_ref["counts"],
        )
        is_breach = bool(psi > psi_threshold) or not np.isfinite(psi)
        per_feature[col] = {
            "psi": None if not np.isfinite(psi) else float(psi),
            "breached": is_breach,
            "threshold": psi_threshold,
        }
        if is_breach:
            breached.append(col)

    psis = [v["psi"] for v in per_feature.values() if isinstance(v.get("psi"), int | float)]
    max_psi = float(max(psis)) if psis else None
    return {
        "psi_threshold": psi_threshold,
        "n_rows": int(len(features)),
        "features": per_feature,
        "breached_features": breached,
        "any_above_threshold": bool(breached),
        "max_psi": max_psi,
    }


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def run_drift_check(
    *,
    input_path: Path | str,
    reference_path: Path | str,
    report_path: Path | str | None = None,
    psi_threshold: float = DEFAULT_PSI_THRESHOLD,
) -> dict[str, Any]:
    frame = _read_table(Path(input_path))
    reference = load_reference(reference_path)
    report = compute_drift_report(frame, reference, psi_threshold=psi_threshold)
    report["input_path"] = str(input_path)
    report["reference_path"] = str(reference_path)
    if report_path is not None:
        out = Path(report_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        logger.info("Wrote drift report to %s (breached=%s)", out, report["any_above_threshold"])
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PSI feature drift vs training reference")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--report", type=Path, default=Path("artifacts/drift_report.json"))
    parser.add_argument("--psi-threshold", type=float, default=DEFAULT_PSI_THRESHOLD)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    report = run_drift_check(
        input_path=args.input,
        reference_path=args.reference,
        report_path=args.report,
        psi_threshold=args.psi_threshold,
    )
    print(json.dumps(report, indent=2))
    return 1 if report["any_above_threshold"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
