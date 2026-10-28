# Interview preparation

Expand this file after each milestone with concrete answers tied to **this**
repo’s implementation. Milestone 0 answers focus on foundations and mindset.

---

## Two-minute project pitch

> ModelOps is a portfolio MLOps platform. I’m building it incrementally like a
> real team: Git hygiene, docs, and verification before features. The first
> workload uses NYC TLC yellow taxi data for a fare-related regression problem,
> with a path to FastAPI serving, MLflow lifecycle, Docker, CI, monitoring, and
> optional GCP deployment. Right now I’ve completed the repository foundation—
> Python 3.12 packaging, tooling, and documentation skeleton—and I’m about to
> implement bounded data ingestion and a sklearn baseline.

## Five-minute pitch (add after Milestone 1+)

Cover: problem framing and leakage, pipeline, metrics, gates, serving
separation, how you’d rollback a bad model.

---

## Beginner questions

**Q: What is MLOps?**
A: Practices that take ML from notebooks to reliable production systems—
versioning, testing, deployment, monitoring, and rollback for data and models.

**Q: Why not train inside a `/predict` request?**
A: Latency, resource cost, non-determinism, and no controlled evaluation. Training
is an offline (or scheduled) job; serving loads an approved artifact.

**Q: What belongs in `.gitignore` for ML projects?**
A: Secrets, virtualenvs, raw datasets, model binaries, local MLflow stores,
Terraform state, caches.

---

## Intermediate questions

**Q: What is target leakage?**
A: Using information that would not be available at prediction time, which
inflates offline metrics and fails in production.

**Q: Health vs readiness?**
A: Health = process alive. Readiness = dependencies (like the model) are loaded
and the instance should receive traffic.

**Q: Why time-based splits for taxi trips?**
A: Trips are temporal; random splits can train on future patterns and overstate
generalization.

---

## Advanced / troubleshooting scenarios

**Q: MAE looks great in training but users complain in production. What do you check?**
A: Serving/training skew, data drift, label delay, wrong approved model, leakage
in offline eval, segment-level errors (borough, hour, weather proxies).

**Q: Candidate model fails the gate. What happens?**
A: Do not promote. Keep serving the previous approved model. Inspect data and
training diffs; fix; re-run.

**Q: Why sklearn before deep learning?**
A: Faster iteration, easier explanation, sufficient for tabular baselines, clearer
failure modes for a platform demo.

---

## Technology “why” prompts

Be ready to defend: Python 3.12, pandas/PyArrow, sklearn, MLflow, FastAPI,
Ruff/pytest, Docker, Prometheus, Cloud Run vs GKE, Terraform.

---

## Reliability / security prompts

- Least-privilege IAM
- Non-root containers
- No secrets in images
- Input validation
- Safe error responses
- Avoid untrusted pickle sources
