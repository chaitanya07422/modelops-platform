# Local development

**Verified:** Milestone 0 tooling + Milestone 1 data/training path on Python 3.12.14.

---

## Environment setup

```bash
cd "/path/to/modelops-platform-folder-first"

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev,ml]"

cp .env.example .env
```

Confirm:

```bash
python --version
python -c "import modelops, pandas, sklearn; print(modelops.__version__)"
```

---

## Dependency groups

| Extra | Purpose | When |
|-------|---------|------|
| `dev` | pytest, ruff, httpx | Always |
| `ml` | pandas, pyarrow, sklearn, joblib, PyYAML | Milestone 1+ |
| `api` | FastAPI stack | Milestone 2+ |
| `tracking` | MLflow | Milestone 3+ |
| `all` | union | Full local stack |

### Version notes

- **Python 3.12 only** — pinned in `requires-python`.
- **pandas 2.2 / PyArrow 19** — TLC Parquet readers.
- **scikit-learn 1.6** — Pipeline, Ridge, metrics.
- **Ruff / pytest** — lint and deterministic tests.

---

## Configuration

- Defaults: `configs/default.yaml`
- Overrides: `.env` / `MODELOPS_*` (see `.env.example`)
- Important knobs: `MODELOPS_TAXI_YEAR`, `MODELOPS_TAXI_MONTH`, `MODELOPS_MAX_ROWS`, `MODELOPS_TRAIN_FRACTION`

---

## Dataset download

```bash
python -m modelops.data
# or: python -m modelops.data --force
```

Writes `data/raw/yellow_tripdata_YYYY-MM.parquet`. If the network fails, place the file manually — **do not fabricate trips**.

---

## Train baseline

```bash
python -m modelops.training --download-if-missing
# or point at a file:
python -m modelops.training --data data/raw/yellow_tripdata_2024-01.parquet
# fixture-only (tests / offline):
python -m modelops.training --data data/fixtures/synthetic_yellow_trips.parquet
```

Outputs (gitignored):

- `models/candidates/baseline_linear_regression.joblib`
- `models/candidates/baseline_linear_regression.metrics.json`
- `data/processed/model_frame_latest.parquet`

---

## Test and lint

```bash
ruff check src tests scripts
ruff format --check src tests scripts
pytest
```

Tests use the synthetic fixture only — no TLC download required.

---

## MLflow + promotion (Milestone 3)

```bash
python -m pip install -e ".[dev,ml,api,tracking]"

python -m modelops.training --download-if-missing
python -m modelops.lifecycle compare --limit 5
python -m modelops.lifecycle promote
python -m modelops.lifecycle rollback   # if needed

mlflow ui --backend-store-uri ./mlruns
```

`mlruns/` is gitignored.

## Prediction API (Milestone 2+)

```bash
# After promote, API prefers models/approved/model.joblib
python -m modelops.api --host 127.0.0.1 --port 8000
# OpenAPI: http://127.0.0.1:8000/docs
```

If approved is missing, the app may fall back to the candidate with a warning.

## Docker

Planned in Milestone 4.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Download `RuntimeError` | Network / CDN | Retry or copy Parquet into `data/raw/` manually |
| `FileNotFoundError` on train | Missing raw file | `--download-if-missing` or `--data` |
| Poor metrics | Expected for zone-only baseline | See `docs/DATASET_AND_MODEL.md` |
| Import errors | Wrong venv / extras | `pip install -e ".[dev,ml]"` |
