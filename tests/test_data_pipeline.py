"""Deterministic tests for ingestion, cleaning, features, and splits."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from modelops.data.features import (
    FEATURE_COLUMNS,
    LEAKAGE_PRONE_COLUMNS,
    TARGET_COLUMN,
    build_model_frame,
)
from modelops.data.load import load_taxi_parquet
from modelops.data.split import time_based_split
from modelops.data.validate import validate_and_clean

_REPO = Path(__file__).resolve().parents[1]
FIXTURE = _REPO / "data" / "fixtures" / "synthetic_yellow_trips.parquet"


@pytest.fixture(scope="module")
def raw_fixture() -> pd.DataFrame:
    assert FIXTURE.exists(), "synthetic fixture missing; regenerate under data/fixtures/"
    return load_taxi_parquet(FIXTURE)


def test_load_respects_max_rows(raw_fixture: pd.DataFrame) -> None:
    capped = load_taxi_parquet(FIXTURE, max_rows=10)
    assert len(capped) == 10
    assert len(raw_fixture) >= 10


def test_validate_drops_invalid_fares_and_durations(raw_fixture: pd.DataFrame) -> None:
    clean, report = validate_and_clean(raw_fixture)
    assert report.input_rows == len(raw_fixture)
    assert report.output_rows == len(clean)
    assert report.output_rows < report.input_rows
    assert (clean["fare_amount"] > 0).all()
    assert report.dropped.get("fare_out_of_range", 0) >= 1
    assert report.dropped.get("invalid_duration", 0) >= 1


def test_feature_frame_excludes_leakage_columns(raw_fixture: pd.DataFrame) -> None:
    clean, _ = validate_and_clean(raw_fixture)
    model_frame = build_model_frame(clean)
    for col in LEAKAGE_PRONE_COLUMNS:
        assert col not in model_frame.columns
    for col in FEATURE_COLUMNS:
        assert col in model_frame.columns
    assert TARGET_COLUMN in model_frame.columns
    # trip_distance exists in raw/clean but must not survive into features
    assert "trip_distance" in clean.columns
    assert "trip_distance" not in model_frame.columns


def test_time_based_split_is_chronological(raw_fixture: pd.DataFrame) -> None:
    clean, _ = validate_and_clean(raw_fixture)
    model_frame = build_model_frame(clean)
    train, test = time_based_split(model_frame, train_fraction=0.8)
    assert len(train) + len(test) == len(model_frame)
    assert train["tpep_pickup_datetime"].max() <= test["tpep_pickup_datetime"].min()


def test_time_based_split_rejects_bad_fraction(raw_fixture: pd.DataFrame) -> None:
    clean, _ = validate_and_clean(raw_fixture)
    model_frame = build_model_frame(clean)
    with pytest.raises(ValueError):
        time_based_split(model_frame, train_fraction=1.0)
