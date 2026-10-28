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
| 5 | Continuous integration | Planned |
| 6 | Monitoring and observability | Planned |
| 7 | Cloud deployment (approval required) | Planned |
| 8 | Terraform (approval required) | Planned |
| 9 | Advanced platform capabilities | Planned |
| 10 | Portfolio and interview readiness | Planned |

## Milestone 4 checklist

- [x] Multi-stage Dockerfile (venv builder, non-root runtime)
- [x] `.dockerignore` and Compose service (read-only model mount)
- [x] Image build + container smoke (`/health`, `/ready`, `/predict`)
- [x] Docs updated

## Rules carried into every milestone

1. Small change → test → document → commit.
2. Never claim metrics, deploys, or tests passed without evidence.
3. No paid cloud resources without explicit approval.
4. Wait for human approval before starting the next milestone.
