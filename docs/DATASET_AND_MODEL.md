# Dataset and model

**Status:** Placeholder for Milestone 1. No TLC month has been downloaded or
inspected in this repository yet. Do not invent schema details or metrics.

---

## Source

- **Publisher:** NYC Taxi & Limousine Commission (TLC)
- **Page:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Format (typical):** Parquet trip records for yellow taxis by year/month
- **Chosen month / download date / exact URL:** *TBD in Milestone 1*
- **Local path:** `data/raw/` (gitignored)

---

## Prediction target (to be decided in Milestone 1)

Candidates under consideration (not yet selected):

1. **Pre-trip fare-related estimate** — use only features knowable before the trip
   (e.g., pickup time, zones, passenger count, rate code). Target might be a
   fare component that can be justified without post-trip measurements.
2. **Post-trip fare modeling** — if the scenario is “after completion,” document
   which fields are legitimate inputs and that this is **not** a pre-trip quote.

**Hard rule:** Exclude tip, tolls, final payment totals, or other fields that
encode the answer when the product story says “estimate before knowing them.”

Assumptions, limitations, and leakage analysis will be written here after
inspection of a real sample.

---

## Schema and quality

Milestone 1 will record:

- Columns, dtypes, units
- Missing-value rates
- Invalid records (e.g., non-positive fares, impossible timestamps)
- Filtering rules and row counts before/after

---

## Split strategy

Prefer a **time-based** train/evaluation split for trip data unless a different
strategy is explicitly justified. Random splits can leak future patterns into
training and inflate reported metrics.

---

## Baseline model

Planned: `sklearn.pipeline.Pipeline` with preprocessing + `LinearRegression`.
A Random Forest comparison follows only after the baseline path works.

## Metrics (definitions only until real runs exist)

| Metric | Meaning | Units | Limitation |
|--------|---------|-------|------------|
| MAE | Average absolute error | Same as target | Treats all errors equally |
| RMSE | Root mean squared error | Same as target | Penalizes large errors more; scale-sensitive |
| R² | Variance explained vs mean baseline | Unitless | Can mislead with skewed targets or leakage |

**Measured results:** none yet.

## Quality gates

Configurable thresholds in `configs/default.yaml` / env vars. Unset until a
baseline evaluation produces honest numbers.

## Reproducibility checklist (Milestone 1+)

- [ ] Dataset month + URL + download date
- [ ] `max_rows` / sample policy
- [ ] Random seed(s)
- [ ] Package versions from `pyproject.toml`
- [ ] Train/eval split definition
- [ ] Actual metric table from a logged run
