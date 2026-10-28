"""Data ingestion, validation, features, and splitting."""

from modelops.data.download import download_yellow_taxi_month
from modelops.data.features import FEATURE_COLUMNS, TARGET_COLUMN, build_model_frame
from modelops.data.load import load_taxi_parquet
from modelops.data.split import time_based_split
from modelops.data.validate import validate_and_clean

__all__ = [
    "FEATURE_COLUMNS",
    "TARGET_COLUMN",
    "build_model_frame",
    "download_yellow_taxi_month",
    "load_taxi_parquet",
    "time_based_split",
    "validate_and_clean",
]
