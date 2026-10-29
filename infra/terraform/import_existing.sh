#!/usr/bin/env bash
# Import live Milestone 7 resources into Terraform state (idempotent skips).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ ! -f terraform.tfvars ]]; then
  echo "Create terraform.tfvars from terraform.tfvars.example first." >&2
  exit 1
fi

PROJECT_ID="$(terraform console <<< 'var.project_id' 2>/dev/null | tr -d '"' || true)"
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == *"Error"* ]]; then
  PROJECT_ID="$(awk -F'"' '/^project_id/{print $2}' terraform.tfvars)"
fi
REGION="$(awk -F'"' '/^region/{print $2; exit}' terraform.tfvars)"
REGION="${REGION:-us-central1}"
REPO="$(awk -F'"' '/^artifact_repo_id/{print $2; exit}' terraform.tfvars)"
REPO="${REPO:-modelops}"
BUCKET="$(awk -F'"' '/^model_bucket_name/{print $2; exit}' terraform.tfvars)"
BUCKET="${BUCKET:-${PROJECT_ID}-models}"
SERVICE="$(awk -F'"' '/^cloud_run_service/{print $2; exit}' terraform.tfvars)"
SERVICE="${SERVICE:-modelops-api}"
SA_ID="$(awk -F'"' '/^deploy_sa_id/{print $2; exit}' terraform.tfvars)"
SA_ID="${SA_ID:-modelops-github-deploy}"

import_one() {
  local addr="$1"
  local id="$2"
  if terraform state show "${addr}" >/dev/null 2>&1; then
    echo "skip (in state): ${addr}"
    return 0
  fi
  echo "import: ${addr} <- ${id}"
  terraform import -input=false "${addr}" "${id}"
}

echo "==> project=${PROJECT_ID} region=${REGION}"

# APIs
for svc in \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com
do
  import_one "google_project_service.required[\"${svc}\"]" "${PROJECT_ID}/${svc}"
done

import_one "google_artifact_registry_repository.modelops" \
  "projects/${PROJECT_ID}/locations/${REGION}/repositories/${REPO}"

import_one "google_storage_bucket.models" "${BUCKET}"

import_one "google_service_account.github_deploy" \
  "projects/${PROJECT_ID}/serviceAccounts/${SA_ID}@${PROJECT_ID}.iam.gserviceaccount.com"

import_one "google_cloud_run_v2_service.api" \
  "projects/${PROJECT_ID}/locations/${REGION}/services/${SERVICE}"

# IAM members use "project role member" or "bucket role member"
SA_EMAIL="${SA_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
import_one "google_storage_bucket_iam_member.deploy_models_viewer" \
  "b/${BUCKET} roles/storage.objectViewer serviceAccount:${SA_EMAIL}"

import_one "google_project_iam_member.deploy_artifact_writer" \
  "${PROJECT_ID} roles/artifactregistry.writer serviceAccount:${SA_EMAIL}"
import_one "google_project_iam_member.deploy_run_admin" \
  "${PROJECT_ID} roles/run.admin serviceAccount:${SA_EMAIL}"
import_one "google_project_iam_member.deploy_sa_user" \
  "${PROJECT_ID} roles/iam.serviceAccountUser serviceAccount:${SA_EMAIL}"
import_one "google_project_iam_member.deploy_storage_admin" \
  "${PROJECT_ID} roles/storage.objectAdmin serviceAccount:${SA_EMAIL}"
import_one "google_project_iam_member.deploy_ar_admin" \
  "${PROJECT_ID} roles/artifactregistry.admin serviceAccount:${SA_EMAIL}"

import_one "google_cloud_run_v2_service_iam_member.public_invoker" \
  "projects/${PROJECT_ID}/locations/${REGION}/services/${SERVICE} roles/run.invoker allUsers"

echo "IMPORT_OK — run: terraform plan"
