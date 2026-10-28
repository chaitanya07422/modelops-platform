# Architecture

**Status:** Target design. **Data + baseline training path implemented (M1).**
Serving, MLflow, CI, and cloud remain planned.

---

## System overview

```mermaid
flowchart TB
  subgraph repo [Repository]
    Src[src/modelops]
    Configs[configs]
    Tests[tests]
    Docs[docs]
  end

  subgraph data_plane [Data plane - planned]
    Raw[data/raw]
    Processed[data/processed]
    Fixtures[data/fixtures]
  end

  subgraph ml_plane [ML plane - planned]
    Train[Training pipeline]
    MLflow[MLflow tracking / registry]
    Approved[Approved model artifact]
  end

  subgraph serve_plane [Serving plane - planned]
    API[FastAPI]
    Batch[Batch jobs]
  end

  subgraph ops_plane [Ops plane - planned]
    CI[GitHub Actions]
    Prom[Prometheus]
    Graf[Grafana]
    Cloud[GCP Cloud Run]
    Tf[Terraform]
  end

  Raw --> Train --> MLflow --> Approved
  Approved --> API
  Approved --> Batch
  API --> Prom --> Graf
  CI --> Cloud
  Tf --> Cloud
```

---

## Component responsibilities (planned)

| Component | Responsibility |
|-----------|----------------|
| Ingestion | Download/load bounded TLC Parquet; record provenance |
| Validation | Schema + quality checks; fail with clear errors |
| Features | Fit transforms on train only; persist for serving parity |
| Training | sklearn Pipeline; seeds; metrics |
| Quality gates | Block promotion when thresholds fail |
| MLflow | Params, metrics, artifacts, model versions/aliases |
| FastAPI | Online predict; health/ready/metrics/model-info |
| Batch | Offline scoring over files/tables |
| CI | Lint, test, image build |
| Monitoring | Request SLIs + drift / quality signals |
| Terraform | Optional cloud resources with destroy path |

---

## Flows

### Training (Milestone 1 implemented; MLflow in Milestone 3)

1. Download/load raw month (or capped sample) — `python -m modelops.data`.
2. Validate and build features — `validate_and_clean` / `build_model_frame`.
3. Time-based split — `time_based_split`.
4. Fit Ridge pipeline; write candidate joblib + metrics JSON.
5. *(Planned M3)* Log to MLflow; run quality gate; promote to approved.

### Online inference (Milestone 2)

1. Process starts; load approved model once.
2. `/ready` fails until load succeeds.
3. `/predict` validates input, scores, returns prediction + model metadata.
4. Errors map to safe HTTP statuses without stack traces.

### Batch inference (Milestone 9)

Offline job reads a feature table, applies the same approved model, writes scores.

---

## Artifact storage

- Local: `models/`, `artifacts/`, file-backed MLflow (`mlruns/`) — all gitignored.
- Cloud (later): Artifact Registry for containers; object storage patterns as needed.

---

## Security boundaries

- Untrusted: client HTTP payloads.
- Trusted: approved model path configured by operators.
- Secrets: env / secret manager only; never in Git or images.
- Do not load arbitrary untrusted pickle from the internet.

---

## Design trade-offs

| Choice | Alternative | Why default |
|--------|-------------|-------------|
| sklearn baseline first | Deep learning day one | Explainability + faster iteration |
| File MLflow locally | Always-on tracking server | Zero infra for learning path |
| Cloud Run before GKE | Kubernetes first | Lower ops cost; K8s later as extension |
| `src/` layout | Flat package | Cleaner packaging; avoids import accidents |

## Failure scenarios (preview)

- Missing approved model → API not ready; clear log.
- Schema change in TLC feed → validation fails before train.
- Gate failure → candidate not promoted; previous approved remains.
- Cloud deploy mistake → rollback to prior revision (documented in M7).
