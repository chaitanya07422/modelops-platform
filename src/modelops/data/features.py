"""Feature engineering for the pre-trip fare_amount scenario.

Only columns knowable when a rider requests a trip with a known destination
zone and pickup time are used. Post-trip measurements (distance, duration,
tips, tolls, totals) are excluded to prevent target leakage.
"""

from __future__ import annotations

import pandas as pd

TARGET_COLUMN = "fare_amount"

# Model inputs after engineering (pre-trip available).
FEATURE_COLUMNS = (
    "passenger_count",
    "PULocationID",
    "DOLocationID",
    "pickup_hour",
    "pickup_dow",
    "pickup_day",
)

# Columns that must never enter the feature matrix for this scenario.
LEAKAGE_PRONE_COLUMNS = (
    "trip_distance",
    "tpep_dropoff_datetime",
    "tip_amount",
    "tolls_amount",
    "total_amount",
    "extra",
    "mta_tax",
    "improvement_surcharge",
    "congestion_surcharge",
    "Airport_fee",
    "airport_fee",
    "cbd_congestion_fee",
    "payment_type",
    "VendorID",
    "store_and_fwd_flag",
    "RatecodeID",  # final rate at end of trip; we already filtered to standard
)


def build_model_frame(clean_trips: pd.DataFrame) -> pd.DataFrame:
    """Derive time features and return feature + target columns only."""
    frame = clean_trips.copy()
    pickup = frame["tpep_pickup_datetime"]
    frame["pickup_hour"] = pickup.dt.hour.astype("int16")
    frame["pickup_dow"] = pickup.dt.dayofweek.astype("int16")
    frame["pickup_day"] = pickup.dt.day.astype("int16")

    # Keep pickup timestamp for time-based splitting; strip before model fit.
    keep = ["tpep_pickup_datetime", *FEATURE_COLUMNS, TARGET_COLUMN]
    missing = [col for col in keep if col not in frame.columns]
    if missing:
        raise ValueError(f"Cannot build model frame; missing columns: {missing}")

    model_frame = frame.loc[:, keep].copy()
    model_frame["passenger_count"] = model_frame["passenger_count"].astype("float64")
    model_frame["PULocationID"] = model_frame["PULocationID"].astype("int32")
    model_frame["DOLocationID"] = model_frame["DOLocationID"].astype("int32")
    model_frame[TARGET_COLUMN] = model_frame[TARGET_COLUMN].astype("float64")
    return model_frame
