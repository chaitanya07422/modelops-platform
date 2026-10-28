# Local development

**Verified in Milestone 0:** Python 3.12 venv, editable install with `[dev]`,
Ruff, and pytest smoke tests. Other sections are planned.

---

## Environment setup

```bash
cd "/path/to/modelops-platform folder first"

# Prefer an explicit 3.12 interpreter
python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

cp .env.example .env
```

Confirm:

```bash
python --version          # expect Python 3.12.x
python -c "import modelops; print(modelops.__version__)"
```

---

## Dependency groups

| Extra | Purpose | When |
|-------|---------|------|
| `dev` | pytest, ruff, httpx | Milestone 0+ |
| `ml` | pandas, pyarrow, sklearn, … | Milestone 1+ |
| `api` | FastAPI, uvicorn, pydantic | Milestone 2+ |
| `tracking` | MLflow | Milestone 3+ |
| `all` | union of the above | When you need the full stack |

### Version choices (why these pins)

- **Python 3.12 only** — Narrow range avoids surprise breaks from 3.13 wheels.
- **Ruff 0.11.x** — Single tool for lint + format; replaces many flake8 plugins.
- **pytest 8.x** — Current stable; used with `pythonpath = src`.
- **ML / API / MLflow pins** — Locked in `pyproject.toml` before first install of
  each extra so environments stay reproducible. Adjust pins only with a tested
  commit and a short note in the changelog/commit message.

---

## Configuration

- Defaults: `configs/default.yaml`
- Overrides: environment variables listed in `.env.example`
- Never commit `.env`

---

## Planned commands (not implemented yet)

```bash
# Milestone 1
# python -m modelops.data.download ...
# python -m modelops.training.train ...

# Milestone 2
# uvicorn modelops.api.app:app --reload --port 8000

# Milestone 3
# mlflow ui --backend-store-uri ./mlruns
```

---

## Test and lint (Milestone 0)

```bash
ruff check src tests
ruff format --check src tests
ruff format src tests          # apply formatting if needed
pytest
pytest -q --cov=modelops      # optional coverage once you want it
```

---

## Docker / Compose

Planned in Milestone 4. Do not expect `docker compose up` to work yet.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Wrong Python version | Shell `python3` → 3.9 | Use `python3.12` for venv |
| Import errors | Package not installed editable | `pip install -e ".[dev]"` |
| Ruff/pytest missing | Dev extra not installed | Same as above |
| Want ML libs early | Optional | `pip install -e ".[ml]"` after understanding why |
