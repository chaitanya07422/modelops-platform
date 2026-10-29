# CI/CD and deployment

**Status:** Milestone 5 CI **implemented**. Cloud deploy remains planned (Milestone 7).

---

## GitHub Actions — `CI` workflow

File: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

| Trigger | Branches |
|---------|----------|
| `push` | `main` |
| `pull_request` | targeting `main` |

Concurrency: one in-flight run per ref; newer pushes cancel older runs.

### Jobs

| Job | What it runs | Notes |
|-----|--------------|-------|
| `lint` | `ruff check`, `ruff format --check` | Python 3.12; pinned Ruff |
| `test` | `pip install -e ".[dev,ml,api,tracking]"` then `pytest -q` | Uses synthetic fixture only — **no TLC download** |
| `docker` | Build `Dockerfile` via Buildx | Runs after lint+test; **does not push** the image |

Permissions are least-privilege: `contents: read` only.

### What CI deliberately does *not* do

- Download NYC TLC Parquet from the network
- Require GCP credentials or secrets
- Push images to Artifact Registry
- Deploy to Cloud Run
- Run Compose smoke tests that need a mounted approved model (image **build** only)

### Local equivalent

```bash
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev,ml,api,tracking]"
ruff check src tests scripts
ruff format --check src tests scripts
pytest -q
docker compose build api   # optional; needs Docker Desktop
```

---

## Image tagging (current vs planned)

| Now (M5) | Later (M7) |
|----------|------------|
| Tag `modelops-api:ci-<sha>` locally in the Actions job | Push to Artifact Registry with git SHA tags |
| `push: false` | Push only from trusted `main` with OIDC/WIF |

Never embed secrets in image layers.

---

## Release / deploy strategy (planned — Milestone 7)

1. `main` CI green
2. Build + push image to Artifact Registry
3. Deploy Cloud Run revision
4. Smoke: `/health`, `/ready`, sample `/predict`
5. Rollback: route traffic to previous revision

**No cloud deploy will run until you approve cost and credentials.**

---

## Secrets

- CI today needs **no** repository secrets.
- Prefer workload identity federation over long-lived JSON keys when cloud deploy lands.
- Rotate any future secrets; never commit `.env` or service-account keys.

---

## Branch protection (recommended)

In GitHub → Settings → Branches → rule for `main`:

1. Require a pull request before merging
2. Require status checks to pass: `Lint (Ruff)`, `Test (pytest)`, `Docker build`
3. Do not allow force-pushes to `main`

Until those rules are enabled, merges can bypass CI — enable them when you are ready.

---

## Verifying this milestone

- Workflow YAML is in-repo and reviewed.
- The same lint/test commands are run locally before commit.
- A live Actions run on GitHub confirms the workflow after push/PR (environment-dependent).
