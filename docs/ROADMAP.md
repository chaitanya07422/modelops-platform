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
| 7 | Cloud deployment + CD (GCP free-tier / credits) | **In progress** |
| 8 | Terraform (approval required) | Planned |
| 9 | Advanced platform capabilities | Planned |
| 10 | Portfolio and interview readiness | Planned |

## Milestone 7 checklist

- [x] Artifact Registry + Cloud Run deploy script
- [x] Cloud Run Dockerfile with baked approved model
- [x] Teardown script + cost controls (scale to zero)
- [x] Docs (CI/CD + cloud)
- [x] WIF setup script + GCS model upload for GitHub CD
- [x] Deploy job on push to `main` (WIF → GCS → Cloud Build → Cloud Run)
- [x] One-time: run `gcp_wif_setup.sh`, set GitHub secrets, `gcp_upload_model.sh`
- [ ] Live CD smoke verified on `modelops-platform` (needs merge/push to `main`)

- [ ] Commit / PR

## Rules carried into every milestone

1. Small change → test → document → commit.
2. Never claim metrics, deploys, or tests passed without evidence.
3. No paid cloud resources without explicit approval (M7 uses free-tier credits with teardown).
4. Wait for human approval before starting the next milestone.
