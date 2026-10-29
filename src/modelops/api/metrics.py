"""Prometheus metrics for the prediction API.

Labels stay low-cardinality: HTTP method, route template, coarse status class,
and prediction outcome — never zone IDs, free-text features, or user identifiers.
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "modelops_http_requests_total",
    "Total HTTP requests handled by the ModelOps API",
    labelnames=("method", "handler", "status_code"),
)

REQUEST_LATENCY = Histogram(
    "modelops_http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=("method", "handler"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

PREDICTION_COUNT = Counter(
    "modelops_predictions_total",
    "Prediction attempts by outcome",
    labelnames=("outcome",),
)

PREDICTION_VALUE = Histogram(
    "modelops_prediction_fare_usd",
    "Predicted fare_amount distribution in USD",
    buckets=(1, 5, 10, 15, 20, 30, 50, 75, 100, 150, 250),
)

MODEL_READY = Gauge(
    "modelops_model_ready",
    "1 if an approved/candidate model is loaded and ready, else 0",
)


def record_prediction(*, outcome: str, value: float | None = None) -> None:
    """Record a prediction attempt. ``outcome`` is a small fixed vocabulary."""
    PREDICTION_COUNT.labels(outcome=outcome).inc()
    if value is not None and outcome == "success":
        PREDICTION_VALUE.observe(value)


def set_model_ready(ready: bool) -> None:
    MODEL_READY.set(1 if ready else 0)


def metrics_payload() -> tuple[bytes, str]:
    """Return Prometheus exposition body and content type."""
    return generate_latest(), CONTENT_TYPE_LATEST
