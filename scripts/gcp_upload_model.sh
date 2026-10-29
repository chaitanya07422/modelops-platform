#!/usr/bin/env bash
# Upload local approved model artifacts to GCS (source of truth for GitHub CD).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${CLOUDSDK_PYTHON:-}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    export CLOUDSDK_PYTHON="$(command -v python3.12)"
  elif command -v python3.11 >/dev/null 2>&1; then
    export CLOUDSDK_PYTHON="$(command -v python3.11)"
  fi
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
MODEL_BUCKET="${MODEL_BUCKET:-${PROJECT_ID}-models}"
PREFIX="${PREFIX:-approved}"

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

echo "==> Uploading to gs://${MODEL_BUCKET}/${PREFIX}/"
gcloud storage cp \
  models/approved/model.joblib \
  models/approved/model.metrics.json \
  "gs://${MODEL_BUCKET}/${PREFIX}/" \
  --project="${PROJECT_ID}"

echo "UPLOAD_OK"
echo "gs://${MODEL_BUCKET}/${PREFIX}/model.joblib"
echo "gs://${MODEL_BUCKET}/${PREFIX}/model.metrics.json"
