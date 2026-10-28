# ModelOps prediction API — multi-stage, non-root, serve-only image.
# Model artifacts are mounted at runtime (see docker-compose.yml).

FROM python:3.12.14-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/venv \
    && pip install --upgrade pip

COPY pyproject.toml README.md ./
COPY src ./src

# Serve image needs ML + API only (no MLflow / pytest / ruff).
RUN pip install ".[ml,api]"


FROM python:3.12.14-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODELOPS_ENV=production \
    MODELOPS_API_HOST=0.0.0.0 \
    MODELOPS_API_PORT=8000 \
    MODELOPS_APPROVED_MODEL_PATH=/models/approved/model.joblib \
    MODELOPS_MODEL_PATH=/models/approved/model.joblib \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH="/app/src"

WORKDIR /app

# curl for HEALTHCHECK; no compilers in the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 modelops \
    && useradd --system --uid 10001 --gid modelops --create-home --home-dir /home/modelops modelops

COPY --from=builder /opt/venv /opt/venv
COPY --chown=modelops:modelops pyproject.toml README.md ./
COPY --chown=modelops:modelops src ./src
COPY --chown=modelops:modelops configs ./configs

# Empty mount points for model artifacts (bind-mounted at run time).
RUN mkdir -p /models/approved /models/candidates \
    && chown -R modelops:modelops /models /app

USER modelops

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${MODELOPS_API_PORT}/health" || exit 1

CMD ["sh", "-c", "uvicorn modelops.api.app:app --host ${MODELOPS_API_HOST} --port ${MODELOPS_API_PORT}"]
