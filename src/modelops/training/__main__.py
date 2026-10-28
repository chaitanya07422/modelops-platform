"""CLI: ``python -m modelops.training`` runs the baseline training pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from modelops.config import load_config
from modelops.data.download import download_yellow_taxi_month
from modelops.training.train import train_baseline, train_result_to_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the ModelOps baseline fare model")
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help="Path to yellow taxi Parquet (default: configured raw path)",
    )
    parser.add_argument(
        "--download-if-missing",
        action="store_true",
        help="Attempt TLC download when --data / raw file is missing",
    )
    parser.add_argument("--model-out", type=Path, default=None, help="joblib output path")
    parser.add_argument("--metrics-out", type=Path, default=None, help="metrics JSON output path")
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Skip MLflow tracking (still writes candidate artifacts)",
    )
    parser.add_argument(
        "--register-model",
        action="store_true",
        help="Also register the sklearn model in the MLflow Model Registry",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_config()
    data_path = args.data or config.raw_parquet_path

    if not data_path.exists():
        if not args.download_if_missing:
            logging.error(
                "Data file missing at %s. Pass --download-if-missing or provide --data.",
                data_path,
            )
            return 1
        try:
            download_yellow_taxi_month(config)
        except Exception as exc:  # noqa: BLE001 - CLI boundary
            logging.error("Download failed: %s", exc)
            return 1
        data_path = config.raw_parquet_path

    try:
        result = train_baseline(
            data_path=data_path,
            config=config,
            model_output=args.model_out,
            metrics_output=args.metrics_out,
            log_mlflow=not args.no_mlflow,
            register_model=args.register_model,
        )
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        logging.error("%s", exc)
        return 1

    print(json.dumps(train_result_to_dict(result), indent=2))
    if result.gate is not None and not result.gate.passed:
        logging.warning("Training finished but quality gate FAILED — do not promote")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
