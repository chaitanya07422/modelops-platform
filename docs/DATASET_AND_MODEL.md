# Dataset and model

**Status:** Milestone 1 implemented and locally verified.

---

## Source and provenance

| Field | Value |
|-------|-------|
| Publisher | NYC Taxi & Limousine Commission (TLC) |
| Page | https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page |
| Data dictionary | [Yellow Trips Data Dictionary (PDF)](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf) |
| Dataset | Yellow taxi trip records |
| Month | **2024-01** |
| Download URL | `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet` |
| Download date (UTC) | **2026-10-28T16:08:36Z** (local verification run) |
| Local path | `data/raw/yellow_tripdata_2024-01.parquet` (gitignored) |
| Local row cap | `MODELOPS_MAX_ROWS=50000` (first N rows in file order for local speed) |

The full January 2024 file is ~50 MB. Local training uses a configurable cap so laptops stay responsive. The evaluation split is still **time-based among cleaned rows**, not a random reshuffle of the month.

---

## Prediction scenario

**Intended use:** Pre-trip **metered fare** estimate when the rider (or app) knows:

- Approximate pickup time
- Pickup TLC zone
- Drop-off TLC zone (destination stated up front)

**Target:** `fare_amount` — time-and-distance fare calculated by the meter (USD), **before** tips, tolls, and most surcharges.

**Not claimed:** An authoritative NYC fare quote, a total-with-tips estimator, or a production pricing engine.

### Why this target

`fare_amount` is the core metered charge documented by TLC. Predicting `total_amount` would mix tips, tolls, and surcharges that depend on payment behavior and route details beyond a simple zone pair. Predicting tip is a different product problem.

### Feature availability (pre-trip)

| Used feature | Available pre-trip? | Notes |
|--------------|---------------------|-------|
| `PULocationID` | Yes | Pickup zone |
| `DOLocationID` | Yes | Destination zone stated by rider |
| `passenger_count` | Usually | Self-reported / requested |
| `pickup_hour` / `pickup_dow` / `pickup_day` | Yes | From requested pickup time |

### Explicitly excluded (leakage / post-trip)

| Column | Why excluded |
|--------|----------------|
| `trip_distance` | Actual meter distance — known after the trip (apps would use a **routing estimate**, not this column) |
| `tpep_dropoff_datetime` / duration | Known after completion |
| `tip_amount`, `tolls_amount`, `total_amount` | Payment outcome / totals |
| `extra`, `mta_tax`, `improvement_surcharge`, `congestion_surcharge`, `Airport_fee` | Fare components entangled with trip outcome / location rules; left out of v1 baseline |
| `payment_type` | Often finalized at payment time |
| `RatecodeID` | Dictionary: *final* rate at end of trip; we **filter** to standard rate (`1`) then drop it from features |
| `VendorID`, `store_and_fwd_flag` | Not rider-facing pre-trip inputs for this scenario |

### Filter: standard rate only

Rows with `RatecodeID != 1` are dropped. Flat airport / negotiated fares make `fare_amount` nearly deterministic from rate code and would muddy a zone+time baseline.

---

## Cleaning rules (Milestone 1)

Applied in order by `modelops.data.validate.validate_and_clean`:

1. Non-null required fields
2. `RatecodeID == 1`
3. `fare_amount` in `(0.01, 250]`
4. `passenger_count` in `[1, 6]`
5. Location IDs in `[1, 265]`
6. Duration in `(1, 180)` minutes

### Verified cleaning counts (50 000-row local sample)

| Stage | Rows |
|-------|------|
| Input | 50 000 |
| Dropped non-standard ratecode | 3 719 |
| Dropped fare out of range | 721 |
| Dropped passenger out of range | 488 |
| Dropped invalid duration | 345 |
| **Output** | **44 727** |

---

## Train / evaluation split

- **Strategy:** time-based on `tpep_pickup_datetime`
- **Fraction:** 80% earlier trips → train; 20% later → eval
- **Verified sizes:** train 35 781 / test 8 946

Random splits are avoided so future patterns do not leak into training.

---

## Baseline model

- `sklearn.pipeline.Pipeline`
- `ColumnTransformer`: `StandardScaler` on numeric time/passenger fields; `OneHotEncoder(handle_unknown="ignore")` on zone IDs
- Estimator: **`Ridge(alpha=1.0)`** (linear baseline)

**Why Ridge instead of OLS `LinearRegression`:** one-hot zone IDs create a wide, collinear matrix. Unregularized least squares was numerically unstable in local experiments. Ridge remains a linear model and is the honest engineering choice here. A Random Forest comparison is deferred to a later phase.

Artifact (gitignored): `models/candidates/baseline_linear_regression.joblib`

Metrics sidecar (gitignored): `models/candidates/baseline_linear_regression.metrics.json`

---

## Metrics — measured results

Definitions:

| Metric | Meaning | Units | Limitation |
|--------|---------|-------|------------|
| MAE | Average absolute error | USD | Treats all errors equally |
| RMSE | Root mean squared error | USD | Emphasizes large misses |
| R² | Variance explained vs predicting the mean | unitless | Can look strong with leakage or weak with hard segments |

### Held-out results (time-based test set)

Recorded **2026-10-28T16:08:37Z** on the local sample above:

| Metric | Value |
|--------|-------|
| MAE | **5.63** USD |
| RMSE | **8.61** USD |
| R² | **0.570** |
| Test rows | 8 946 |

Interpretation: on this capped January 2024 sample, the zone+time linear model explains about 57% of held-out fare variance and is typically ~$5–9 off. That is a **learning baseline**, not a product-ready fare API. Omitting actual/`routed` distance is a deliberate honesty trade-off and caps accuracy.

---

## Quality gates

Configurable placeholders live in `configs/default.yaml`. Promotion automation arrives in Milestone 3. Provisional ideas informed by this baseline (not enforced yet):

- `max_mae` ≈ 10 USD
- `max_rmse` ≈ 15 USD
- `min_r2` ≈ 0.3

A candidate must beat configured thresholds **and** remain free of known leakage before any “approved” label.

---

## Synthetic fixture

`data/fixtures/synthetic_yellow_trips.parquet` is **explicitly labeled synthetic** for deterministic tests. It is never a silent stand-in for TLC data in demos.

---

## Reproducibility checklist

- [x] Dataset month + URL + download date
- [x] `max_rows` policy documented
- [x] Seed / config defaults (`random_seed=42`; Ridge is deterministic)
- [x] Package pins in `pyproject.toml` (`modelops[ml]`)
- [x] Time-based split definition
- [x] Actual metric table from a logged local run
- [ ] MLflow run IDs (Milestone 3)
