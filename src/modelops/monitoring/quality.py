"""Delayed ground-truth quality when batch labels arrive."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from modelops.data.features import TARGET_COLUMN
from modelops.training.evaluate import evaluate_regressor

logger = logging.getLogger(__name__)

PREDICTION_COLUMN = "prediction"


def compute_quality_report(
    frame: pd.DataFrame,
    *,
    target_column: str = TARGET_COLUMN,
    prediction_column: str = PREDICTION_COLUMN,
) -> dict[str, Any]:
    """MAE/RMSE/R² when both labels and predictions are present."""
    if target_column not in frame.columns:
        raise ValueError(f"Missing label column {target_column}")
    if prediction_column not in frame.columns:
        raise ValueError(f"Missing prediction column {prediction_column}")

    subset = frame[[target_column, prediction_column]].dropna()
    if subset.empty:
        raise ValueError("No overlapping labeled rows to evaluate")

    metrics = evaluate_regressor(
        subset[target_column].to_numpy(dtype=float),
        subset[prediction_column].to_numpy(dtype=float),
    )
    return {
        "target_column": target_column,
        "prediction_column": prediction_column,
        "metrics": metrics.as_dict(),
        "n_labeled": int(len(subset)),
        "n_rows": int(len(frame)),
    }


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def run_quality_check(
    *,
    predictions_path: Path | str,
    report_path: Path | str | None = None,
) -> dict[str, Any]:
    frame = _read_table(Path(predictions_path))
    report = compute_quality_report(frame)
    report["predictions_path"] = str(predictions_path)
    if report_path is not None:
        out = Path(report_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        logger.info("Wrote quality report to %s", out)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Delayed ground-truth quality vs batch predictions"
    )
    parser.add_argument(
        "--predictions",
        required=True,
        type=Path,
        help="Scored table with fare_amount + prediction columns",
    )
    parser.add_argument("--report", type=Path, default=Path("artifacts/quality_report.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    report = run_quality_check(predictions_path=args.predictions, report_path=args.report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
