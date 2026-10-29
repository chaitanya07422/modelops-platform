#!/usr/bin/env bash
# Milestone 7 — enable APIs, push image to Artifact Registry, deploy Cloud Run.
# Requires: gcloud auth, billing on the project, models/approved/model.joblib
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer a modern Python for the Cloud SDK when the system default is 3.9.
if [[ -z "${CLOUDSDK_PYTHON:-}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    export CLOUDSDK_PYTHON="$(command -v python3.12)"
  elif command -v python3.11 >/dev/null 2>&1; then
    export CLOUDSDK_PYTHON="$(command -v python3.11)"
  fi
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-modelops}"
SERVICE="${SERVICE:-modelops-api}"
IMAGE_NAME="${IMAGE_NAME:-modelops-api}"
TAG="${TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo latest)}"
MODEL_BUCKET="${MODEL_BUCKET:-${PROJECT_ID}-models}"
# Keep GCS in sync with local approved model so GitHub CD can bake the same artifact.
UPLOAD_MODEL="${UPLOAD_MODEL:-1}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set PROJECT_ID or run: gcloud config set project YOUR_PROJECT" >&2
  exit 1
fi

if [[ ! -f models/approved/model.joblib ]]; then
  echo "Missing models/approved/model.joblib — train and promote first." >&2
  exit 1
fi
if [[ ! -f models/approved/model.metrics.json ]]; then
  echo "Missing models/approved/model.metrics.json — promote should write this sidecar." >&2
  exit 1
fi

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:${TAG}"

echo "==> Project=${PROJECT_ID} Region=${REGION} Service=${SERVICE}"
echo "==> Image=${IMAGE}"

echo "==> Enabling required APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

if [[ "${UPLOAD_MODEL}" == "1" ]]; then
  echo "==> Syncing approved model to gs://${MODEL_BUCKET}/approved/"
  MODEL_BUCKET="${MODEL_BUCKET}" PROJECT_ID="${PROJECT_ID}" \
    "${ROOT}/scripts/gcp_upload_model.sh"
fi
echo "==> Ensuring Artifact Registry repo '${REPO}'"
if ! gcloud artifacts repositories describe "${REPO}" \
  --location="${REGION}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="ModelOps API images" \
    --project="${PROJECT_ID}"
fi

echo "==> Building and pushing via Cloud Build"
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --config=cloudbuild.yaml \
  --substitutions="_REGION=${REGION},_REPO=${REPO},_IMAGE=${IMAGE_NAME},_TAG=${TAG}" \
  .

echo "==> Deploying Cloud Run (min instances 0, small footprint)"
gcloud run deploy "${SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=0 \
  --max-instances=2 \
  --concurrency=40 \
  --timeout=60 \
  --set-env-vars="MODELOPS_ENV=production,MODELOPS_LOG_LEVEL=INFO,MODELOPS_APPROVED_MODEL_PATH=/models/approved/model.joblib,MODELOPS_MODEL_PATH=/models/approved/model.joblib" \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format='value(status.url)')"

echo ""
echo "DEPLOY_OK"
echo "URL=${URL}"
echo "==> Smoke"
curl -fsS "${URL}/health" && echo
curl -fsS "${URL}/ready" && echo
curl -fsS "${URL}/predict" \
  -H 'Content-Type: application/json' \
  -d '{"passenger_count":1,"PULocationID":161,"DOLocationID":236,"pickup_hour":8,"pickup_dow":2,"pickup_day":15}' \
  && echo
echo ""
echo "Teardown: ./scripts/gcp_teardown.sh"
echo "Docs: docs/CI_CD_AND_DEPLOYMENT.md"
