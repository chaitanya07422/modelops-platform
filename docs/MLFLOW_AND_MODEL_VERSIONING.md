# MLflow and model versioning

**Status:** Planned for Milestone 3. No tracking server or runs exist yet.

---

## Concepts

| Concept | Simple definition |
|---------|-------------------|
| Experiment | Named container for related runs |
| Run | One execution with params, metrics, tags, artifacts |
| Artifact | File logged with a run (model, plots, reports) |
| Model version | Registered immutable model snapshot |
| Alias / stage | Pointer such as `champion` / `candidate` (MLflow 2.x aliases preferred) |

**Why it matters:** Without tracking, you cannot explain which data, code, and
hyperparameters produced a production model.

---

## Planned local setup

```bash
export MLFLOW_TRACKING_URI=file:./mlruns
# after Milestone 3 training exists:
# mlflow ui --backend-store-uri ./mlruns
```

`mlruns/` is gitignored.

---

## Candidate vs approved

1. Training produces a **candidate**.
2. Quality gates evaluate the candidate on held-out data.
3. Only a passing candidate is **promoted** to approved (file path and/or registry alias).
4. Serving loads **approved** only.

## Promotion and rollback (planned procedure)

- Promotion: record metrics, artifact URI, git SHA, dataset provenance, then flip alias/path.
- Rollback: point alias/path back to previous known-good version; restart or rely on new ready checks.
- Never delete the prior approved artifact until rollback window passes.

## Reproducibility

Log: package versions, seed, data month/URL, config path, split definition, metrics.
