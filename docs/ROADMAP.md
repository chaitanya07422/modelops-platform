# Roadmap

This file tracks milestone intent versus what has actually been verified.

**Legend**

- **Done** — implemented, locally verified, and committed.
- **In progress** — current work.
- **Planned** — not started; do not treat as available.

| Milestone | Title | Status |
|-----------|-------|--------|
| 0 | Repository foundation | **Done** |
| 1 | Data ingestion and baseline ML | **Done** (verified: fixture tests + TLC sample train) |
| 2 | FastAPI inference service | Planned |
| 3 | MLflow and model lifecycle | Planned |
| 4 | Docker and reproducibility | Planned |
| 5 | Continuous integration | Planned |
| 6 | Monitoring and observability | Planned |
| 7 | Cloud deployment (approval required) | Planned |
| 8 | Terraform (approval required) | Planned |
| 9 | Advanced platform capabilities | Planned |
| 10 | Portfolio and interview readiness | Planned |

## Milestone 1 checklist

- [x] TLC dictionary reviewed; January 2024 sample downloaded
- [x] Target = `fare_amount` (pre-trip scenario); leakage columns documented
- [x] Validation, features, time-based split
- [x] Ridge linear baseline in sklearn Pipeline
- [x] MAE / RMSE / R² measured on held-out time split
- [x] Deterministic synthetic fixture tests
- [x] Docs updated (`DATASET_AND_MODEL`, local dev, README)

## Rules carried into every milestone

1. Small change → test → document → commit.
2. Never claim metrics, deploys, or tests passed without evidence.
3. No paid cloud resources without explicit approval.
4. Wait for human approval before starting the next milestone.
