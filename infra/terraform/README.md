# ModelOps Terraform (Milestone 8)

Declarative GCP resources that match the Milestone 7 Cloud Run stack.

| Resource | Terraform | Also managed by |
|----------|-----------|-----------------|
| APIs | `apis.tf` | `gcp_deploy.sh` / WIF setup |
| Artifact Registry `modelops` | `artifact_registry.tf` | CD / deploy script |
| GCS models bucket | `gcs.tf` | `gcp_upload_model.sh` |
| Deploy SA + core IAM | `iam.tf` | `gcp_wif_setup.sh` |
| Cloud Run `modelops-api` | `cloud_run.tf` | **GitHub CD** (image ignored in TF) |
| Cloud Monitoring dashboard | `monitoring.tf` | Console charts for Cloud Run |

WIF pool/provider remain in [`scripts/gcp_wif_setup.sh`](../../scripts/gcp_wif_setup.sh) for now (OIDC attribute conditions are awkward in pure TF without churn).

## Prerequisites

- Terraform `>= 1.5` (e.g. binary in `~/.local/bin` if Homebrew/Xcode blocks the HashiCorp tap)
- GCP auth for the provider, either:
  - `gcloud auth application-default login`, or
  - `export GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token)"` (works when ADC needs reauth)
- Existing project with billing / free-trial credits

## First-time against the live project

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # gitignored
# edit project_id / bucket if needed

terraform init
./import_existing.sh                           # imports live M7 resources into state
terraform plan
terraform apply                                # only after plan looks right
```

`import_existing.sh` is idempotent-ish: skip resources already in state.

## Coexistence with CD

Cloud Run **image** changes from GitHub Actions are ignored by Terraform
(`lifecycle.ignore_changes`). Scaling, env vars, and IAM still belong here.

Do **not** `terraform destroy` unless you intend to tear down the demo stack
(or use `./scripts/gcp_teardown.sh` for Cloud Run only).

## Cost

Keep `min_instances = 0`, small CPU/memory. Destroy or teardown when demos finish.
