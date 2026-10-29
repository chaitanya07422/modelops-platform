# Terraform and cloud

**Status:** Milestone 7 uses **imperative** `gcloud` scripts (`gcp_deploy.sh`,
`gcp_wif_setup.sh`, `gcp_upload_model.sh`) plus GitHub Actions CD on `main`.
Milestone 8 will express the same resources in Terraform.

**Hard rule:** Do not `terraform apply` or create extra paid GCP resources without
explicit approval. M7 Cloud Run was approved against free-tier / trial credits —
always run teardown when demos finish.

---

## Why infrastructure as code

Declarative resources (Artifact Registry, Cloud Run, IAM) are reviewable,
repeatable, and destroyable. Click-ops demos do not survive interviews or
incident recovery.

---

## Planned resources (illustrative)

- GCP project reference (bring-your-own project)
- Artifact Registry repository for container images
- Cloud Run service for the API
- Service accounts with **least privilege**
- Optional: Secret Manager references

## State

- Remote state (GCS backend) recommended before team use
- Local state only for throwaway learning sandboxes
- State files are secrets-adjacent — never commit them (gitignored)

## Cost controls

- Keep Cloud Run scaled to zero when idle where possible
- Use small CPU/memory for demos
- Set budgets/alerts in GCP before experiments
- Always document `terraform destroy` / service delete steps in the milestone
  that introduces apply instructions

## IAM sketch

- Deploy SA: push images + update Cloud Run
- Runtime SA: read model objects only if stored in GCS; no project-wide admin

## Recovery

- Destroy path tested in a scratch project first
- Keep previous container revision for rollback
