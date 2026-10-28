# Terraform and cloud

**Status:** Planned for Milestones 7–8.

**Hard rule:** Do not `terraform apply` or create paid GCP resources without
explicit approval. This document exists so you understand cost and cleanup
*before* anything is provisioned.

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
