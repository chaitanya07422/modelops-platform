# GitHub Actions

| Workflow | File | Purpose |
|----------|------|---------|
| CI (+ CD on main) | `ci.yml` | Ruff, pytest, Docker build; **Deploy Cloud Run** only on push to `main` |

## Triggers

| Event | Jobs |
|-------|------|
| Pull request → `main` | lint, test, docker |
| Push to `main` | lint, test, docker, deploy |

## Continuous deploy prerequisites

1. `./scripts/gcp_wif_setup.sh` in the GCP project
2. GitHub repository **Actions secrets**:
   - `GCP_PROJECT_ID`
   - `GCP_REGION` (optional; job defaults to `us-central1` if empty)
   - `GCP_SERVICE_ACCOUNT`
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_MODEL_BUCKET`
3. `./scripts/gcp_upload_model.sh` so `gs://$GCP_MODEL_BUCKET/approved/` has the model

Auth is Workload Identity Federation (`id-token: write`). No JSON service-account key files in the repo.

Details: [docs/CI_CD_AND_DEPLOYMENT.md](../../docs/CI_CD_AND_DEPLOYMENT.md).
