# Scripts

| Script | Purpose |
|--------|---------|
| `download_taxi_data.py` | Wrapper → `python -m modelops.data` |
| `train_baseline.py` | Wrapper → `python -m modelops.training` |
| `generate_synthetic_fixture.py` | Rebuild `data/fixtures/synthetic_yellow_trips.parquet` |

Prefer the `python -m modelops.*` entry points after `pip install -e ".[dev,ml]"`.
