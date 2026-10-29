# Roadmap

This file tracks milestone intent versus what has actually been verified.

**Legend**

- **Done** — implemented, locally verified, and committed.
- **In progress** — current work.
- **Planned** — not started; do not treat as available.

| Milestone | Title | Status |
|-----------|-------|--------|
| 0 | Repository foundation | **Done** |
| 1 | Data ingestion and baseline ML | **Done** |
| 2 | FastAPI inference service | **Done** |
| 3 | MLflow and model lifecycle | **Done** |
| 4 | Docker and reproducibility | **Done** |
| 5 | Continuous integration | **Done** |
| 6 | Monitoring and observability | **Done** |
| 7 | Cloud deployment + CD (GCP free-tier / credits) | **Done** |
| 8 | Terraform IaC | **Done** |
| 9 | Batch inference + drift + delayed quality | **Done** |
| 10 | Portfolio and interview readiness | Planned |

## Milestone 9 checklist

- [x] Batch score CLI (`python -m modelops.batch`)
- [x] Training/promote writes `reference_features.json`
- [x] PSI drift CLI (`python -m modelops.monitoring.drift`)
- [x] Delayed ground-truth quality CLI (`python -m modelops.monitoring.quality`)
- [x] Pytest coverage
- [x] Docs + README
- [x] Commit / PR (#5)

## Rules carried into every milestone

1. Small change → test → document → commit.
2. Never claim metrics, deploys, or tests passed without evidence.
3. No paid cloud resources without explicit approval (M7/M8 use free-tier credits with teardown).
4. Wait for human approval before starting the next milestone.
