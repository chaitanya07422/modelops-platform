# Monitoring and reliability

**Status:** Planned for Milestone 6 (service metrics) and Milestone 9 (drift /
model quality). Nothing is scraped or dashboarded yet.

---

## Layers

| Layer | Examples | Question answered |
|-------|----------|-------------------|
| Service | QPS, latency, 5xx, saturation | Is the API healthy? |
| Model input | Feature distributions, null rates | Did the world change? |
| Model quality | MAE vs delayed ground truth | Is the model still useful? |

**Data drift** — input distribution shifts.
**Concept drift** — relationship between inputs and target shifts.

---

## Planned tooling

- Structured application logs (JSON or key=value; no full sensitive payloads)
- Prometheus `/metrics`
- Grafana dashboard JSON in-repo (Milestone 6)
- Drift jobs comparing training reference vs live/batch windows (Milestone 9)

## Operational responses (preview)

| Signal | First response |
|--------|----------------|
| Spike in 5xx | Check ready/model load, recent deploy |
| Latency rise | Check payload size, model complexity, resource limits |
| Feature drift | Inspect upstream data; consider retrain |
| Quality drop | Rollback approved model; open retrain |

## Common production failures

- Deployed container without model artifact
- Schema change not reflected in Pydantic models
- Training/serving skew (different preprocessing)
- Alert fatigue from high-cardinality metric labels
