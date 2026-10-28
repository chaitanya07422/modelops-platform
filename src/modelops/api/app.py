"""FastAPI application factory for ModelOps online inference."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from modelops import __version__
from modelops.api.deps import model_service
from modelops.api.model_service import ModelLoadError
from modelops.api.routes import router
from modelops.config import load_config

logger = logging.getLogger(__name__)


def _resolve_model_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    config = load_config()
    approved = config.approved_model_path
    if approved.exists():
        return approved
    # Until Milestone 3 promotion exists, fall back to the local candidate artifact.
    candidate = config.candidate_dir / "baseline_linear_regression.joblib"
    if candidate.exists():
        logger.warning(
            "Approved model missing at %s; using candidate %s for local serving",
            approved,
            candidate,
        )
        return candidate
    return approved


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the configured model once at startup; mark not-ready on failure."""
    model_path = Path(app.state.model_path)
    metrics_path = getattr(app.state, "metrics_path", None)
    try:
        model_service.load(model_path, metrics_path=metrics_path)
    except ModelLoadError:
        # Process stays up for /health; /ready and /predict return 503.
        logger.error("Startup model load failed; service will report not ready")
    yield


def create_app(
    *,
    model_path: Path | str | None = None,
    metrics_path: Path | str | None = None,
) -> FastAPI:
    """Build the ASGI app.

    Parameters
    ----------
    model_path:
        Optional override (tests). Defaults to ``MODELOPS_MODEL_PATH`` /
        ``configs/default.yaml`` approved path.
    metrics_path:
        Optional metrics JSON sidecar override.
    """
    resolved_model = _resolve_model_path(Path(model_path) if model_path else None)
    resolved_metrics = Path(metrics_path) if metrics_path else None

    app = FastAPI(
        title="ModelOps Prediction API",
        version=__version__,
        description=(
            "Online inference for the ModelOps taxi fare baseline. "
            "Demo estimates only — not official TLC quotes."
        ),
        lifespan=lifespan,
    )
    app.state.model_path = resolved_model
    app.state.metrics_path = resolved_metrics

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        # Avoid echoing full payloads; return sanitized validation errors only.
        del request
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        del exc
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(router)
    return app


# Default ASGI entrypoint: ``uvicorn modelops.api.app:app``
app = create_app()
