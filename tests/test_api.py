"""API integration tests — use a fixture-trained model; no TLC download."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from modelops.api.app import create_app
from modelops.api.deps import model_service
from modelops.config import load_config
from modelops.training.train import train_baseline

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "synthetic_yellow_trips.parquet"


@pytest.fixture(scope="module")
def trained_paths(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("api_model")
    model_out = root / "model.joblib"
    metrics_out = root / "model.metrics.json"
    config = load_config(repo_root=REPO)
    train_baseline(
        data_path=FIXTURE,
        config=config,
        model_output=model_out,
        metrics_output=metrics_out,
    )
    return model_out, metrics_out


@pytest.fixture
def client(trained_paths: tuple[Path, Path]) -> TestClient:
    model_path, metrics_path = trained_paths
    application = create_app(model_path=model_path, metrics_path=metrics_path)
    with TestClient(application) as test_client:
        yield test_client
    # Reset singleton so later tests start clean.
    model_service.pipeline = None
    model_service.load_error = None
    model_service.metadata = {}
    model_service.model_path = None


@pytest.fixture
def client_without_model(tmp_path: Path) -> TestClient:
    missing = tmp_path / "does-not-exist.joblib"
    application = create_app(model_path=missing)
    with TestClient(application) as test_client:
        yield test_client
    model_service.pipeline = None
    model_service.load_error = None
    model_service.metadata = {}
    model_service.model_path = None


def test_health_always_ok(client_without_model: TestClient) -> None:
    response = client_without_model.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_fails_without_model(client_without_model: TestClient) -> None:
    response = client_without_model.get("/ready")
    assert response.status_code == 503


def test_ready_ok_with_model(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["model_loaded"] is True


def test_model_info(client: TestClient) -> None:
    response = client.get("/model-info")
    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["target"] == "fare_amount"
    assert "PULocationID" in body["features"]
    assert body["model_path"] == "model.joblib"
    # Must not expose absolute developer paths.
    assert "/" not in (body["model_path"] or "")


def test_predict_success(client: TestClient) -> None:
    payload = {
        "passenger_count": 1,
        "PULocationID": 10,
        "DOLocationID": 20,
        "pickup_hour": 8,
        "pickup_dow": 2,
        "pickup_day": 5,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "prediction" in body
    assert isinstance(body["prediction"], float)
    assert body["target"] == "fare_amount"
    assert body["currency"] == "USD"
    assert "not an official" in body["disclaimer"].lower()


def test_predict_validation_error(client: TestClient) -> None:
    response = client.post(
        "/predict",
        json={
            "passenger_count": 99,
            "PULocationID": 10,
            "DOLocationID": 20,
            "pickup_hour": 8,
            "pickup_dow": 2,
            "pickup_day": 5,
        },
    )
    assert response.status_code == 422


def test_predict_not_ready(client_without_model: TestClient) -> None:
    response = client_without_model.post(
        "/predict",
        json={
            "passenger_count": 1,
            "PULocationID": 10,
            "DOLocationID": 20,
            "pickup_hour": 8,
            "pickup_dow": 2,
            "pickup_day": 5,
        },
    )
    assert response.status_code == 503
    assert "stack" not in response.text.lower()
    assert "Traceback" not in response.text
