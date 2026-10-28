# Roadmap

This file tracks milestone intent versus what has actually been verified.

**Legend**

- **Done** — implemented, locally verified, and committed.
- **In progress** — current work.
- **Planned** — not started; do not treat as available.

| Milestone | Title | Status |
|-----------|-------|--------|
| 0 | Repository foundation | **Done** (verified locally: ruff + pytest) |
| 1 | Data ingestion and baseline ML | Planned |
| 2 | FastAPI inference service | Planned |
| 3 | MLflow and model lifecycle | Planned |
| 4 | Docker and reproducibility | Planned |
| 5 | Continuous integration | Planned |
| 6 | Monitoring and observability | Planned |
| 7 | Cloud deployment (approval required) | Planned |
| 8 | Terraform (approval required) | Planned |
| 9 | Advanced platform capabilities | Planned |
| 10 | Portfolio and interview readiness | Planned |

## Milestone 0 checklist

- [x] Inspect workspace / initialize Git without destroying work
- [x] Feature branch for foundation work
- [x] `.gitignore`, `.env.example`, `pyproject.toml`
- [x] `src/modelops` package shell + smoke tests
- [x] Initial README and docs skeleton
- [x] Local `pip install -e ".[dev]"`, Ruff, pytest (2 passed; lint/format clean on Python 3.12.14)

## Rules carried into every milestone

1. Small change → test → document → commit.
2. Never claim metrics, deploys, or tests passed without evidence.
3. No paid cloud resources without explicit approval.
4. Wait for human approval before starting the next milestone.
