# Terraform and cloud

**Status:** Milestone 7 (imperative scripts + GitHub CD) is **Done**.
Milestone 8 Terraform lives in [`infra/terraform/`](../infra/terraform/).

**Hard rule:** Do not `terraform apply` / `destroy` or create extra paid GCP
resources without explicit approval. Keep free-tier / trial posture and tear
down when demos finish.

---

## Why infrastructure as code

Declarative resources (Artifact Registry, Cloud Run, IAM, GCS) are reviewable,
repeatable, and destroyable. Click-ops demos do not survive interviews or
incident recovery.

---

## What Terraform manages (M8)

| Resource | File |
|----------|------|
| Required Google APIs | `apis.tf` |
| Artifact Registry `modelops` | `artifact_registry.tf` |
| Models GCS bucket | `gcs.tf` |
| Deploy SA + project IAM | `iam.tf` |
| Cloud Run `modelops-api` (+ public invoker) | `cloud_run.tf` |

**Still scripted:** Workload Identity pool/provider (`scripts/gcp_wif_setup.sh`).
**Still CD-owned:** container image digest on each push to `main` (Terraform
`ignore_changes` on the image).

---

## Apply / import / destroy

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # gitignored — set project_id
terraform init
./import_existing.sh                           # if resources already exist from M7
terraform plan
terraform apply                                # only when plan is intentional
```

Teardown options:

```bash
# Cloud Run only (keep images / bucket)
./scripts/gcp_teardown.sh

# Full stack declared in Terraform (careful — deletes AR/GCS/SA bindings too)
cd infra/terraform && terraform destroy
```

---

## State

- Default: **local** state (gitignored `*.tfstate`) for the learning sandbox.
- Before team use: switch to a GCS backend (commented stub in `versions.tf`).
- Never commit state or `terraform.tfvars`.

---

## Cost controls

- Cloud Run `min_instances = 0`, `512Mi`, `max_instances = 2`
- Budget alerts in GCP Billing
- Destroy or teardown when demos finish

---

## IAM sketch

- Deploy SA (`modelops-github-deploy`): Artifact Registry, Cloud Run admin,
  storage object admin/viewer, serviceAccountUser — impersonated via WIF from GitHub
- Runtime SA: default Compute Engine SA on Cloud Run (baked model; no GCS read at runtime)

---

## Recovery

- Prefer previous Cloud Run revision for app rollback
- Re-run `import_existing.sh` if state is lost but cloud resources remain
- Keep `gcp_teardown.sh` for a fast Cloud Run-only delete
