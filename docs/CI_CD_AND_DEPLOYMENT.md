# CI/CD and deployment

**Status:** Milestone 5 CI **implemented**. Milestone 6 monitoring is **local/Compose** (not a cloud deploy). Cloud deploy remains planned (Milestone 7).

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
| `test` | `pip install -e ".[dev,ml,api,tracking]"` then `pytest -q` | Uses synthetic fixture only — **no TLC download**; covers `/metrics` |
| `docker` | Build `Dockerfile` via Buildx | Runs after lint+test; **does not push** the image |

Permissions are least-privilege: `contents: read` only.

`prometheus-client` ships with the `api` extra, so CI already installs metrics deps. Tests assert `/metrics` returns Prometheus text; CI does **not** start Prometheus or Grafana.

### What CI deliberately does *not* do

- Download NYC TLC Parquet from the network
- Require GCP credentials or secrets
- Push images to Artifact Registry
- Deploy to Cloud Run
- Run Compose smoke tests that need a mounted approved model (image **build** only)
- Bring up the Compose `monitoring` profile (Prometheus/Grafana)

### Local equivalent

```bash
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev,ml,api,tracking]"
ruff check src tests scripts
ruff format --check src tests scripts
pytest -q
docker compose build api   # optional; needs Docker Desktop
```

Optional monitoring stack (Docker Desktop required):

```bash
docker compose --profile monitoring up -d
# Prometheus :9090  |  Grafana :3000 (admin/admin)  |  API /metrics scraped by Prometheus
```

Details: [MONITORING_AND_RELIABILITY.md](MONITORING_AND_RELIABILITY.md).

---

## Monitoring vs deploy

| Layer | Where it lives | CI / deploy today |
|-------|----------------|-------------------|
| App metrics (`/metrics`) | FastAPI + `prometheus-client` | Tested in pytest; image includes the endpoint |
| Prometheus + Grafana | Compose profile `monitoring` | Local only; not started in Actions |
| Cloud scrape / alerts | Milestone 7+ | Not configured |

Release smoke (when M7 lands) should include `/health`, `/ready`, sample `/predict`, and optionally `/metrics` content-type checks — still no requirement to run Grafana in the cloud path unless you approve that stack.

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
4. Smoke: `/health`, `/ready`, sample `/predict` (optional `/metrics`)
5. Rollback: route traffic to previous revision

**No cloud deploy will run until you approve cost and credentials.**

---

## Secrets

- CI today needs **no** repository secrets.
- Prefer workload identity federation over long-lived JSON keys when cloud deploy lands.
- Rotate any future secrets; never commit `.env` or service-account keys.
- Grafana’s default Compose password is for **local learning only** — change it before any shared or remote use.

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
- Monitoring: pytest covers `/metrics`; Compose profile is optional and documented separately.
