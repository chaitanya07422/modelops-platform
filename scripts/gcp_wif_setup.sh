#!/usr/bin/env bash
# One-time: Workload Identity Federation + deploy SA + models GCS bucket for GitHub CD.
# Requires: gcloud auth with permission to create IAM / buckets in the project.
set -euo pipefail

if [[ -z "${CLOUDSDK_PYTHON:-}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    export CLOUDSDK_PYTHON="$(command -v python3.12)"
  elif command -v python3.11 >/dev/null 2>&1; then
    export CLOUDSDK_PYTHON="$(command -v python3.11)"
  fi
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
GITHUB_REPO="${GITHUB_REPO:-chaitanya07422/modelops-platform}"
POOL_ID="${POOL_ID:-github-pool}"
PROVIDER_ID="${PROVIDER_ID:-github-provider}"
SA_ID="${SA_ID:-modelops-github-deploy}"
MODEL_BUCKET="${MODEL_BUCKET:-${PROJECT_ID}-models}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set PROJECT_ID or run: gcloud config set project YOUR_PROJECT" >&2
  exit 1
fi

PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
SA_EMAIL="${SA_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL_RESOURCE="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}"
PROVIDER_RESOURCE="${POOL_RESOURCE}/providers/${PROVIDER_ID}"
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "==> Project=${PROJECT_ID} (${PROJECT_NUMBER})"
echo "==> GitHub repo=${GITHUB_REPO}"
echo "==> Model bucket=gs://${MODEL_BUCKET}"
echo "==> Deploy SA=${SA_EMAIL}"

echo "==> Enabling APIs"
gcloud services enable \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

echo "==> Creating deploy service account (if missing)"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_ID}" \
    --project="${PROJECT_ID}" \
    --display-name="ModelOps GitHub Actions deploy"
fi

echo "==> Project IAM for deploy SA"
# storage.objectAdmin: Cloud Build source staging + read models bucket (also bound below).
for ROLE in \
  roles/artifactregistry.admin \
  roles/run.admin \
  roles/cloudbuild.builds.editor \
  roles/iam.serviceAccountUser \
  roles/storage.objectAdmin
do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet >/dev/null
done

echo "==> Ensuring Artifact Registry repo modelops"
if ! gcloud artifacts repositories describe modelops \
  --location="${REGION}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud artifacts repositories create modelops \
    --repository-format=docker \
    --location="${REGION}" \
    --description="ModelOps API images" \
    --project="${PROJECT_ID}"
fi

# Cloud Build default SA must push images; Compute SA is often the Cloud Run runtime identity.
echo "==> IAM for Cloud Build / Compute SAs"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer" \
  --condition=None \
  --quiet >/dev/null || true

gcloud iam service-accounts add-iam-policy-binding "${COMPUTE_SA}" \
  --project="${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser" \
  --quiet >/dev/null || true

echo "==> Ensuring models bucket gs://${MODEL_BUCKET}"
if ! gcloud storage buckets describe "gs://${MODEL_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${MODEL_BUCKET}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi

gcloud storage buckets add-iam-policy-binding "gs://${MODEL_BUCKET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectViewer" \
  --quiet >/dev/null

echo "==> Workload Identity Pool"
if ! gcloud iam workload-identity-pools describe "${POOL_ID}" \
  --project="${PROJECT_ID}" \
  --location=global >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${POOL_ID}" \
    --project="${PROJECT_ID}" \
    --location=global \
    --display-name="GitHub Actions pool"
fi

echo "==> GitHub OIDC provider"
if ! gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
  --project="${PROJECT_ID}" \
  --location=global \
  --workload-identity-pool="${POOL_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
    --project="${PROJECT_ID}" \
    --location=global \
    --workload-identity-pool="${POOL_ID}" \
    --display-name="GitHub provider" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository=='${GITHUB_REPO}'"
else
  gcloud iam workload-identity-pools providers update-oidc "${PROVIDER_ID}" \
    --project="${PROJECT_ID}" \
    --location=global \
    --workload-identity-pool="${POOL_ID}" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository=='${GITHUB_REPO}'" \
    --quiet
fi

echo "==> Allow GitHub repo to impersonate deploy SA"
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_RESOURCE}/attribute.repository/${GITHUB_REPO}" \
  --quiet >/dev/null

echo ""
echo "WIF_SETUP_OK"
echo ""
echo "Add these as GitHub Actions secrets (Settings → Secrets and variables → Actions → Secrets),"
echo "or: gh secret set NAME --repo ${GITHUB_REPO}"
echo "  GCP_PROJECT_ID=${PROJECT_ID}"
echo "  GCP_REGION=${REGION}"
echo "  GCP_SERVICE_ACCOUNT=${SA_EMAIL}"
echo "  GCP_WORKLOAD_IDENTITY_PROVIDER=${PROVIDER_RESOURCE}"
echo "  GCP_MODEL_BUCKET=${MODEL_BUCKET}"
echo ""
echo "Then upload the approved model once:"
echo "  MODEL_BUCKET=${MODEL_BUCKET} ./scripts/gcp_upload_model.sh"
echo ""
echo "CD runs on push to main after CI (see .github/workflows/ci.yml deploy job)."
