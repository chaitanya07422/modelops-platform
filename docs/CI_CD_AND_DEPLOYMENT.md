# CI/CD and deployment

**Status:** Planned. Milestone 5 adds GitHub Actions; Milestone 7 adds Cloud Run
deployment docs. No workflows are verified yet.

---

## Planned PR checks

1. Ruff lint + format check
2. pytest (deterministic; no TLC download required)
3. Optional Docker image build (no push from fork PRs)

## Image tagging (planned)

- `git sha` tags for traceability
- `latest` only on main if you explicitly choose that policy
- Never embed secrets in layers

## Release / deploy strategy (planned)

- Main branch green → build image → push Artifact Registry → deploy Cloud Run revision
- Smoke: `/health`, `/ready`, sample `/predict`
- Rollback: traffic to previous Cloud Run revision

## Secrets

- Prefer workload identity federation over long-lived JSON keys in CI
- Repository secrets only when necessary; document rotation

## Branch protection (recommended later)

- Require PR
- Require status checks (lint + test)
- Disallow force-push to `main`

**No cloud deploy will run until you approve cost and credentials.**
