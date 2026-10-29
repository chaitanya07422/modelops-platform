# Scripts

| Script | Purpose |
|--------|---------|
| `download_taxi_data.py` | Wrapper → `python -m modelops.data` |
| `train_baseline.py` | Wrapper → `python -m modelops.training` |
| `generate_synthetic_fixture.py` | Rebuild `data/fixtures/synthetic_yellow_trips.parquet` |
| `docker_smoke.sh` | Build/start Compose API and hit health/ready/predict |
| `gcp_wif_setup.sh` | One-time WIF pool/provider, deploy SA, models GCS bucket |
| `gcp_upload_model.sh` | Upload `models/approved/` → GCS (CD source of truth) |
| `gcp_deploy.sh` | Manual: APIs → upload model (default) → Cloud Build → Cloud Run |
| `gcp_teardown.sh` | Delete Cloud Run (optional: images / AR repo) |

Prefer the `python -m modelops.*` entry points after `pip install -e ".[dev,ml]"`.

### Enable GitHub CD (once)

```bash
./scripts/gcp_wif_setup.sh          # then gh secret set … (printed names)
./scripts/gcp_upload_model.sh       # after train + promote
# merge/push to main → Deploy Cloud Run job
```

Cloud deploy details: [docs/CI_CD_AND_DEPLOYMENT.md](../docs/CI_CD_AND_DEPLOYMENT.md).
