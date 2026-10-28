"""Schema and data-quality checks for yellow taxi trips.

Invalid rows are dropped with explicit counters so filtering decisions stay
auditable in docs and logs — never silently replaced with fabricated data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)

# Standard metered rate only. Flat/negotiated rates make fare_amount nearly
# deterministic from RatecodeID and muddy a pre-trip zone+time baseline.
STANDARD_RATECODE = 1.0

FARE_MIN = 0.01
FARE_MAX = 250.0
PASSENGER_MIN = 1.0
PASSENGER_MAX = 6.0
LOCATION_MIN = 1
LOCATION_MAX = 265


@dataclass
class CleaningReport:
    """Row counts explaining how raw trips became the modeling table."""

    input_rows: int
    dropped: dict[str, int] = field(default_factory=dict)
    output_rows: int = 0

    def as_dict(self) -> dict[str, object]:
        return {
            "input_rows": self.input_rows,
            "dropped": dict(self.dropped),
            "output_rows": self.output_rows,
        }


def _drop_with_reason(
    frame: pd.DataFrame,
    mask_keep: pd.Series,
    reason: str,
    report: CleaningReport,
) -> pd.DataFrame:
    dropped = int((~mask_keep).sum())
    report.dropped[reason] = dropped
    return frame.loc[mask_keep].copy()


def validate_and_clean(frame: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """Validate types/ranges and drop invalid trips.

    Rules (documented in docs/DATASET_AND_MODEL.md):
    - Require non-null pickup/dropoff timestamps and core fields
    - Keep RatecodeID == 1 (standard rate)
    - Positive, bounded fare_amount
    - passenger_count in [1, 6]
    - Valid TLC zone IDs
    - dropoff strictly after pickup
    - Exclude absurdly short/long durations for quality (1 min .. 3 hours)
    """
    report = CleaningReport(input_rows=len(frame))
    out = frame.copy()

    out["tpep_pickup_datetime"] = pd.to_datetime(out["tpep_pickup_datetime"], errors="coerce")
    out["tpep_dropoff_datetime"] = pd.to_datetime(out["tpep_dropoff_datetime"], errors="coerce")

    required = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "RatecodeID",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
    ]
    out = _drop_with_reason(
        out,
        out[required].notna().all(axis=1),
        "missing_required_fields",
        report,
    )

    out = _drop_with_reason(
        out,
        out["RatecodeID"] == STANDARD_RATECODE,
        "non_standard_ratecode",
        report,
    )

    out = _drop_with_reason(
        out,
        out["fare_amount"].between(FARE_MIN, FARE_MAX, inclusive="both"),
        "fare_out_of_range",
        report,
    )

    out = _drop_with_reason(
        out,
        out["passenger_count"].between(PASSENGER_MIN, PASSENGER_MAX, inclusive="both"),
        "passenger_out_of_range",
        report,
    )

    out = _drop_with_reason(
        out,
        out["PULocationID"].between(LOCATION_MIN, LOCATION_MAX)
        & out["DOLocationID"].between(LOCATION_MIN, LOCATION_MAX),
        "invalid_location_id",
        report,
    )

    duration_minutes = (
        out["tpep_dropoff_datetime"] - out["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60.0
    out = _drop_with_reason(
        out,
        (duration_minutes > 1.0) & (duration_minutes < 180.0),
        "invalid_duration",
        report,
    )

    report.output_rows = len(out)
    logger.info("Cleaning report: %s", report.as_dict())
    return out, report
