#!/usr/bin/env bash
# Build and smoke-test the ModelOps API container.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Start Docker Desktop and retry." >&2
  exit 1
fi

if [[ ! -f models/approved/model.joblib ]]; then
  echo "Missing models/approved/model.joblib — train and promote first." >&2
  exit 1
fi

echo "==> Building image"
docker compose build api

echo "==> Starting api"
docker compose up -d api

cleanup() {
  docker compose down >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Waiting for /ready"
for _ in $(seq 1 40); do
  if curl -fsS "http://127.0.0.1:8000/ready" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:8000/health" | tee /tmp/modelops_health.json
echo
curl -fsS "http://127.0.0.1:8000/ready" | tee /tmp/modelops_ready.json
echo
curl -fsS "http://127.0.0.1:8000/model-info" | tee /tmp/modelops_info.json
echo
curl -fsS "http://127.0.0.1:8000/predict" \
  -H 'Content-Type: application/json' \
  -d '{"passenger_count":1,"PULocationID":161,"DOLocationID":236,"pickup_hour":8,"pickup_dow":2,"pickup_day":15}' \
  | tee /tmp/modelops_predict.json
echo
echo "SMOKE_OK"
