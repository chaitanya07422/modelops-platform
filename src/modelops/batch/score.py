"""Batch-score a feature table with the approved sklearn Pipeline."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from modelops.api.model_service import ModelService
from modelops.config import load_config
from modelops.data.features import FEATURE_COLUMNS, TARGET_COLUMN, build_model_frame

logger = logging.getLogger(__name__)

PREDICTION_COLUMN = "prediction"


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    raise ValueError(f"Unsupported input format: {path.suffix} (use .parquet or .csv)")


def _write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        frame.to_parquet(path, index=False)
    elif suffix == ".csv":
        frame.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {path.suffix} (use .parquet or .csv)")


def score_batch(
    *,
    input_path: Path | str,
    output_path: Path | str,
    model_path: Path | str | None = None,
    metrics_path: Path | str | None = None,
) -> dict[str, Any]:
    """Load approved model, score rows, write predictions next to input columns."""
    cfg = load_config()
    in_path = Path(input_path)
    out_path = Path(output_path)
    model = Path(model_path) if model_path else cfg.approved_model_path
    sidecar = Path(metrics_path) if metrics_path else None

    frame = _read_table(in_path)
    if any(col not in frame.columns for col in FEATURE_COLUMNS):
        if "tpep_pickup_datetime" in frame.columns:
            logger.info("Input looks like raw trips; applying build_model_frame()")
            frame = build_model_frame(frame)
        else:
            missing = [col for col in FEATURE_COLUMNS if col not in frame.columns]
            raise ValueError(f"Missing feature columns: {missing}")

    service = ModelService()
    service.load(model, metrics_path=sidecar)
    preds = service.predict_frame(frame)

    result = frame.copy()
    result[PREDICTION_COLUMN] = preds.to_numpy()
    _write_table(result, out_path)

    summary: dict[str, Any] = {
        "input_path": str(in_path),
        "output_path": str(out_path),
        "model_path": str(model),
        "n_rows": int(len(result)),
        "features": list(FEATURE_COLUMNS),
        "prediction_column": PREDICTION_COLUMN,
        "has_labels": TARGET_COLUMN in result.columns,
        "prediction_mean": float(preds.mean()),
        "prediction_std": float(preds.std(ddof=0)) if len(preds) else 0.0,
    }
    summary_path = out_path.with_name(out_path.stem + ".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    logger.info("Batch scored %s rows -> %s", summary["n_rows"], out_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch-score with the approved ModelOps model")
    parser.add_argument("--input", required=True, type=Path, help="Input .parquet or .csv")
    parser.add_argument("--output", required=True, type=Path, help="Output .parquet or .csv")
    parser.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Model joblib (default: models/approved/model.joblib)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    summary = score_batch(input_path=args.input, output_path=args.output, model_path=args.model)
    print(json.dumps(summary, indent=2))
    return 0
