# API reference

**Status:** Milestone 2 API + Milestone 6 `/metrics` implemented.

Base URL (local default): `http://127.0.0.1:8000`

OpenAPI UI: `http://127.0.0.1:8000/docs`

---

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| `GET` | `/health` | Process liveness | None |
| `GET` | `/ready` | Model loaded and scorers ready | None |
| `GET` | `/model-info` | Safe model metadata | None |
| `POST` | `/predict` | Single fare prediction | None |
| `GET` | `/metrics` | Prometheus exposition | None |

---

## Health vs readiness

- **`GET /health`** → `200` if the process is alive. Does **not** check the model.
- **`GET /ready`** → `200` when a sklearn Pipeline is loaded; `503` otherwise.

Orchestrators should restart on failed liveness and stop sending traffic on failed readiness.

---

## `GET /health`

```bash
curl -s http://127.0.0.1:8000/health
```

```json
{"status": "ok"}
```

---

## `GET /ready`

```bash
curl -s http://127.0.0.1:8000/ready
```

Success:

```json
{"status": "ready", "model_loaded": true, "detail": null}
```

Not ready (`503`):

```json
{
  "detail": {
    "status": "not_ready",
    "model_loaded": false,
    "detail": "model_artifact_missing"
  }
}
```

---

## `GET /model-info`

Returns basename of the artifact (not absolute paths), feature list, optional training metrics from the sidecar JSON, and readiness.

```bash
curl -s http://127.0.0.1:8000/model-info
```

---

## `POST /predict`

### Request schema

| Field | Type | Rules |
|-------|------|-------|
| `passenger_count` | number | integer-valued, 1–6 |
| `PULocationID` | integer | 1–265 |
| `DOLocationID` | integer | 1–265 |
| `pickup_hour` | integer | 0–23 |
| `pickup_dow` | integer | 0–6 (Mon=0) |
| `pickup_day` | integer | 1–31 |

### Example

```bash
curl -s http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "passenger_count": 1,
    "PULocationID": 161,
    "DOLocationID": 236,
    "pickup_hour": 8,
    "pickup_dow": 2,
    "pickup_day": 15
  }'
```

Success (`200`):

```json
{
  "prediction": 12.3456,
  "target": "fare_amount",
  "currency": "USD",
  "model_id": "baseline-2024-1",
  "disclaimer": "Learning/demo estimate only — not an official NYC TLC fare quote."
}
```

### Errors

| Status | When |
|--------|------|
| 422 | Pydantic validation failure (ranges / types) |
| 503 | Model not loaded / not ready |
| 500 | Unexpected prediction failure (no stack trace in body) |

Responses never include filesystem secrets or Python tracebacks.

---

## Model loading

- Loaded **once** during application startup (lifespan).
- Path: `MODELOPS_MODEL_PATH` / approved path in config.
- If approved is missing, local servers may fall back to
  `models/candidates/baseline_linear_regression.joblib` (logged warning) until
  Milestone 3 promotion exists.
- Startup load failure keeps the process up for `/health` but `/ready` stays `503`.

---

## `GET /metrics`

```bash
curl -s http://127.0.0.1:8000/metrics | head
```

Prometheus text exposition including request counts/latency, prediction
outcomes, fare histogram, and `modelops_model_ready`. See
[MONITORING_AND_RELIABILITY.md](MONITORING_AND_RELIABILITY.md).

---

## Run locally

```bash
pip install -e ".[dev,ml,api]"
# prefer approved after promote; candidate path works for local demos
export MODELOPS_MODEL_PATH=models/approved/model.joblib
python -m modelops.api --host 127.0.0.1 --port 8000
```
