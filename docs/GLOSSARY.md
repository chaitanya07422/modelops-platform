# Glossary

Alphabetical reference for ML, MLOps, Python packaging, cloud, and reliability
terms used in this project. Expand as milestones introduce new concepts.

---

**Artifact** — File produced by a run or build (model binary, metrics plot, image).

**Batch inference** — Scoring many records offline rather than one HTTP request at a time.

**Candidate model** — Newly trained model awaiting quality gates before approval.

**Concept drift** — Change in the relationship between features and the target.

**Data drift** — Change in input feature distributions relative to a reference.

**Editable install** — `pip install -e .` so source edits apply without reinstall.

**Experiment (MLflow)** — Named group of related training runs.

**Feature** — Model input variable derived from raw data.

**Feature availability** — Whether a feature is knowable at the intended prediction time.

**Gate / quality gate** — Automated check that must pass before promotion.

**Ground truth** — Actual observed target values used for evaluation or monitoring.

**Inference** — Using a trained model to produce predictions.

**Infrastructure as code (IaC)** — Managing cloud resources via versioned config (e.g., Terraform).

**Leakage (target leakage)** — Training with information not available at prediction time.

**MAE** — Mean Absolute Error; average absolute difference between prediction and truth.

**MLflow** — Open-source platform for experiment tracking and model management.

**MLOps** — Practices for reliable ML systems in production.

**Model registry** — Catalog of versioned models with lifecycle metadata/aliases.

**Parquet** — Columnar file format commonly used for analytics datasets (including TLC).

**Pipeline (sklearn)** — Chained preprocessing + estimator fitted/predicted as one object.

**Promotion** — Marking a candidate as the approved model for serving.

**Provenance** — Record of where data/models came from and how they were produced.

**R²** — Coefficient of determination; variance explained versus predicting the mean.

**Readiness** — Signal that an instance can safely receive traffic.

**Regression** — Predicting a continuous numeric target.

**RMSE** — Root Mean Squared Error; quadratic mean of errors.

**Rollback** — Reverting to a previous approved model or application revision.

**Run (MLflow)** — Single tracked execution with params, metrics, and artifacts.

**Schema validation** — Checking columns, types, and constraints before use.

**Serving** — Hosting a model for online or batch predictions.

**Skew (training/serving)** — Mismatch between training-time and serving-time features/code.

**Smoke test** — Minimal test proving a system starts and a basic path works.

**Split (time-based)** — Train/eval partition by time to mimic deployment reality.

**src layout** — Packaging Python code under `src/` to avoid accidental local imports.

**TLC** — NYC Taxi & Limousine Commission; publisher of trip record data.

**Tracking URI** — Location where MLflow stores run metadata (file path or server).
