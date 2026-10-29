# Monitoring and reliability

**Status:** Milestone 6 service metrics **implemented**. Milestone 9 offline
**drift (PSI)** and **delayed ground-truth quality** are **implemented**.

---

## Layers

| Layer | Examples | Question answered | Status |
|-------|----------|-------------------|--------|
| Service | QPS, latency, 5xx, readiness | Is the API healthy? | **Implemented** |
| Model input | Feature PSI vs training reference | Did the world change? | **Implemented (M9)** |
| Model quality | MAE/RMSE vs delayed ground truth | Is the model still useful? | **Implemented (M9)** |

**Data drift** — input distribution shifts.
**Concept drift** — relationship between inputs and target shifts.

---

## Service metrics (Prometheus)

Endpoint: `GET /metrics` (Prometheus text exposition).

| Metric | Type | Labels | Meaning |
|--------|------|--------|---------|
| `modelops_http_requests_total` | counter | `method`, `handler`, `status_code` | Request count |
| `modelops_http_request_duration_seconds` | histogram | `method`, `handler` | Latency |
| `modelops_predictions_total` | counter | `outcome` | `success` / `not_ready` / `error` |
| `modelops_prediction_fare_usd` | histogram | — | Predicted fare distribution |
| `modelops_model_ready` | gauge | — | `1` ready / `0` not |

### Cardinality rules

- `handler` is the **route template** (e.g. `/predict`), never raw URLs with IDs.
- Do **not** label metrics with `PULocationID`, passenger counts, or free text.
- `outcome` is a tiny fixed set.

### Structured request logs

`MetricsMiddleware` logs one line per request:

```text
request method=POST handler=/predict status=200 duration_ms=12.34
```

Request bodies and feature payloads are intentionally omitted.

---

## Local Prometheus + Grafana

Compose uses a `monitoring` profile so the API can run alone:

```bash
# API only
docker compose up -d api

# API + Prometheus + Grafana
docker compose --profile monitoring up -d
```

| Service | URL | Notes |
|---------|-----|-------|
| API metrics | http://127.0.0.1:8000/metrics | Scraped by Prometheus |
| Prometheus | http://127.0.0.1:9090 | Target `api:8000` |
| Grafana | http://127.0.0.1:3000 | Anonymous Viewer; admin/`modelops` |

Dashboard: **ModelOps API** (provisioned from
`monitoring/grafana/dashboards/modelops-api.json`).

Without Docker, run the API locally and scrape with a host Prometheus pointed at
`localhost:8000`, or just `curl /metrics`.

---

## Operational responses

| Signal | First response |
|--------|----------------|
| Spike in 5xx | Check `/ready`, model mount, recent deploy |
| Latency rise | Check payload size, CPU limits, competing load |
| `modelops_model_ready == 0` | Missing/invalid approved artifact; promote or remount |
| Prediction `not_ready` rising | Same as readiness failure |
| Feature drift (`any_above_threshold`) | Inspect upstream data; consider retrain |
| Quality drop (MAE/RMSE rise) | Rollback approved model; open retrain |

---

## Common production failures

- Deployed container without model artifact
- Schema change not reflected in Pydantic models
- Training/serving skew (different preprocessing)
- Alert fatigue from high-cardinality metric labels

---

## Offline drift + quality (Milestone 9)

Training writes `reference_features.json` (quantile histograms). Promote copies it
next to `models/approved/`.

```bash
# Score a feature table with the approved model
python -m modelops.batch \
  --input data/fixtures/synthetic_yellow_trips.parquet \
  --output artifacts/batch_preds.parquet \
  --model models/approved/model.joblib

# PSI vs training reference (exit 1 if any feature > threshold, default 0.25)
python -m modelops.monitoring.drift \
  --input artifacts/batch_preds.parquet \
  --reference models/approved/reference_features.json \
  --report artifacts/drift_report.json

# When fare_amount labels are present on the scored table
python -m modelops.monitoring.quality \
  --predictions artifacts/batch_preds.parquet \
  --report artifacts/quality_report.json
```

**PSI rule of thumb:** &lt; 0.1 stable; 0.1–0.25 moderate; &gt; 0.25 major shift (default fail).

### Still later

- Alertmanager rules wired to paging channels
- Scheduled Cloud Run Jobs / K8s CronJobs for batch+drift
