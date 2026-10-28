"""Load TLC yellow taxi Parquet into pandas with optional row caps."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

# Columns required for the Milestone 1 pre-trip fare scenario.
REQUIRED_COLUMNS = (
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "RatecodeID",
    "PULocationID",
    "DOLocationID",
    "fare_amount",
    "tip_amount",
    "tolls_amount",
    "total_amount",
)


def load_taxi_parquet(path: Path | str, *, max_rows: int | None = None) -> pd.DataFrame:
    """Read a yellow taxi Parquet file, optionally capping rows for local work.

    ``max_rows`` uses Arrow slice semantics (first N row-group rows in file
    order). That is intentional for development speed; evaluation still uses a
    **time-based** split after cleaning, not a random sample of the full month.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Taxi Parquet not found at {path}. Download with "
            "`python -m modelops.data.download` or copy a file into data/raw/."
        )

    logger.info("Loading %s (max_rows=%s)", path, max_rows)
    table = pq.read_table(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in table.column_names]
    if missing:
        raise ValueError(f"Parquet at {path} is missing required columns: {missing}")

    if max_rows is not None and max_rows > 0:
        table = table.slice(0, max_rows)

    frame = table.to_pandas()
    logger.info("Loaded shape=%s", frame.shape)
    return frame
