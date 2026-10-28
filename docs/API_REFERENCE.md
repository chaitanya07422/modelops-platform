# API reference

**Status:** Planned for Milestone 2. No HTTP server is implemented yet.

---

## Planned endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Process liveness |
| `GET` | `/ready` | Model loaded and ready to score |
| `GET` | `/metrics` | Prometheus exposition |
| `POST` | `/predict` | Single validated prediction |
| `GET` | `/model-info` | Safe model version / metadata |

Batch prediction may be a separate CLI/job rather than a large HTTP upload
(decision in Milestone 9).

---

## Health vs readiness

- **`/health`** — “Is the process up?” Used by basic liveness probes.
- **`/ready`** — “Can this instance serve predictions?” Should fail if the
  approved model failed to load or is invalid.

---

## `/predict` (planned)

Request and response schemas will use Pydantic models with:

- Required fields and types
- Reasonable range checks
- Examples in OpenAPI

**Example (placeholder — will not work until Milestone 2):**

```bash
curl -s http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{ "example": true }'
```

---

## Errors (planned)

| Status | When |
|--------|------|
| 422 | Validation failure |
| 503 | Not ready / model unavailable |
| 500 | Unexpected server error (no stack trace to client) |

---

## Metrics (planned)

Prometheus counters/histograms for request count, latency, and errors.
Avoid high-cardinality labels (no raw user IDs or free-text features as labels).
