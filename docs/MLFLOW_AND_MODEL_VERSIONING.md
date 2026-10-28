# MLflow and model versioning

**Status:** Milestone 3 implemented (local file-backed tracking + filesystem promotion).

---

## Concepts

| Concept | Simple definition |
|---------|-------------------|
| Experiment | Named container for related runs (`modelops-taxi-fare`) |
| Run | One training execution with params, metrics, tags, artifacts |
| Artifact | Files logged with a run (joblib, metrics JSON, sklearn flavor) |
| Candidate | Freshly trained model under `models/candidates/` |
| Approved | Serving pointer at `models/approved/model.joblib` |
| History | Prior approved snapshots under `models/approved/history/` |
| Gate | Absolute metric thresholds that must pass before promotion |

**Why it matters:** Without tracking and gates, you cannot explain which data/code
produced a model or stop a bad candidate from reaching the API.

---

## Local MLflow setup

```bash
pip install -e ".[dev,ml,tracking]"

# Default tracking URI: file:<repo>/mlruns (gitignored)
python -m modelops.training --data data/fixtures/synthetic_yellow_trips.parquet

# UI
mlflow ui --backend-store-uri ./mlruns
# open http://127.0.0.1:5000
```

Compare recent runs from the CLI:

```bash
python -m modelops.lifecycle compare --limit 5
```

### What each run logs

- **Params:** model type, alpha, dataset year/month, `max_rows`, split, seeds, row counts
- **Metrics:** `mae`, `rmse`, `r2`, `n_samples`
- **Tags:** scenario, `gate_passed`
- **Artifacts:** candidate `.joblib`, metrics JSON, optional `sklearn_model/` flavor

Optional registry registration:

```bash
python -m modelops.training --data ... --register-model
```

File tracking + filesystem promotion is the primary lifecycle for this portfolio
path. A remote MLflow server can replace `MLFLOW_TRACKING_URI` later without
changing the train/promote APIs.

---

## Quality gates

Configured in `configs/default.yaml` / env:

| Gate | Default | Meaning |
|------|---------|---------|
| `max_mae` | 10.0 | Hold-out MAE must be ≤ this (USD) |
| `max_rmse` | 15.0 | Hold-out RMSE must be ≤ this |
| `min_r2` | 0.3 | Hold-out R² must be ≥ this |

Training embeds a `gate` object in the metrics JSON. Exit code `2` from
`python -m modelops.training` means the model trained but **failed the gate**.
Promotion without `--force` also exits `2` when blocked.

The synthetic pytest fixture often fails `min_r2` under production-like
thresholds — that is intentional. Use the TLC sample (`--download-if-missing`)
for a gate-passing demo, or `--force` only to exercise promote/rollback wiring.

Optional promotion flag `--require-improvement` also demands candidate MAE ≤
current approved MAE.

---

## Candidate vs approved

```text
train  →  models/candidates/*.joblib  (+ MLflow run)
gate   →  pass / fail
promote → models/approved/model.joblib  (API loads this)
rollback ← models/approved/history/<timestamp>/
```

### Promote

```bash
python -m modelops.lifecycle promote
# or with improvement check:
python -m modelops.lifecycle promote --require-improvement
```

On success:

- Copies candidate → `models/approved/model.joblib`
- Writes `models/approved/model.metrics.json` and `CURRENT.json`
- Archives previous approved under `models/approved/history/<UTC>/`

On gate failure: **no copy**; JSON reports `quality_gate_failed`.

### Rollback

```bash
python -m modelops.lifecycle rollback
```

Restores the newest history snapshot. Current approved is saved under
`history/pre_rollback_<UTC>/` before overwrite.

---

## Serving

After promotion, prefer:

```bash
unset MODELOPS_MODEL_PATH   # or point explicitly at approved
python -m modelops.api
```

Resolution order:

1. `MODELOPS_MODEL_PATH` (explicit override)
2. Approved path if present
3. Candidate fallback with a warning (local convenience only)

---

## Reproducibility checklist

- [x] Params + metrics in MLflow
- [x] Dataset month / max_rows / split logged
- [x] Gate thresholds versioned in config
- [x] Promotion writes provenance + archives prior approved
- [x] Rollback path documented and tested
