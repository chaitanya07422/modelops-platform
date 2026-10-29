#!/usr/bin/env bash
# Delete the Milestone 7 Cloud Run service (and optionally images / AR repo).
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
REPO="${REPO:-modelops}"
SERVICE="${SERVICE:-modelops-api}"
DELETE_IMAGES="${DELETE_IMAGES:-0}"
DELETE_REPO="${DELETE_REPO:-0}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set PROJECT_ID or run: gcloud config set project YOUR_PROJECT" >&2
  exit 1
fi

echo "==> Deleting Cloud Run service ${SERVICE} (${REGION})"
gcloud run services delete "${SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --quiet \
  || echo "(service already gone or not found)"

if [[ "${DELETE_IMAGES}" == "1" ]]; then
  echo "==> Deleting images in ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/modelops-api"
  gcloud artifacts docker images delete \
    "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/modelops-api" \
    --project="${PROJECT_ID}" \
    --delete-tags \
    --quiet \
    || echo "(images already gone or not found)"
fi

if [[ "${DELETE_REPO}" == "1" ]]; then
  echo "==> Deleting Artifact Registry repo ${REPO}"
  gcloud artifacts repositories delete "${REPO}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --quiet \
    || echo "(repo already gone or not found)"
fi

echo "TEARDOWN_OK"
echo "Tip: set a GCP budget alert if you have not already (Billing → Budgets)."
