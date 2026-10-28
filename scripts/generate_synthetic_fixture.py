#!/usr/bin/env python3
"""Regenerate the labeled synthetic yellow-taxi fixture used by pytest."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "fixtures" / "synthetic_yellow_trips.parquet"


def main() -> None:
    rng = np.random.default_rng(42)
    n = 200
    pickup = pd.date_range("2024-01-01", periods=n, freq="h")
    duration_min = rng.integers(5, 40, size=n)
    dropoff = pickup + pd.to_timedelta(duration_min, unit="m")
    pu = rng.integers(1, 30, size=n)
    do = rng.integers(1, 30, size=n)
    fare = 3.0 + 0.5 * np.abs(do - pu) + 0.2 * duration_min + rng.normal(0, 0.4, n)
    fare = np.clip(fare, 2.5, 80.0)

    frame = pd.DataFrame(
        {
            "VendorID": np.ones(n, dtype=int),
            "tpep_pickup_datetime": pickup,
            "tpep_dropoff_datetime": dropoff,
            "passenger_count": rng.integers(1, 5, size=n).astype(float),
            "trip_distance": (duration_min / 10.0).astype(float),
            "RatecodeID": np.ones(n, dtype=float),
            "store_and_fwd_flag": ["N"] * n,
            "PULocationID": pu,
            "DOLocationID": do,
            "payment_type": np.ones(n, dtype=int),
            "fare_amount": fare,
            "extra": np.zeros(n),
            "mta_tax": np.full(n, 0.5),
            "tip_amount": rng.uniform(0, 5, n),
            "tolls_amount": np.zeros(n),
            "improvement_surcharge": np.full(n, 0.3),
            "total_amount": fare + 0.8,
            "congestion_surcharge": np.full(n, 2.5),
            "Airport_fee": np.zeros(n),
        }
    )

    bad_fare = frame.iloc[:2].copy()
    bad_fare["fare_amount"] = [-1.0, 9999.0]
    bad_dur = frame.iloc[2:4].copy()
    bad_dur["tpep_dropoff_datetime"] = bad_dur["tpep_pickup_datetime"]
    bad_dur["fare_amount"] = [12.0, 15.0]

    out_frame = pd.concat([bad_fare, bad_dur, frame], ignore_index=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_frame.to_parquet(OUT, index=False)
    print(f"wrote {OUT} rows={len(out_frame)} bytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
