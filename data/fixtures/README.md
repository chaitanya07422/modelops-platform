# Test fixtures

## `synthetic_yellow_trips.parquet`

- **Label:** Synthetic / non-TLC. For deterministic automated tests only.
- **Contents:** ~200 plausible rows plus intentionally invalid fares/durations.
- **Schema:** Mimics yellow taxi columns required by Milestone 1.
- **Not for demos:** Never present as real NYC trip data or as a silent
  replacement when the official TLC download fails.

Regenerate:

```bash
python scripts/generate_synthetic_fixture.py
```
