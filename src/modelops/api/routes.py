"""HTTP routes for health, readiness, prediction, and model metadata."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from modelops.api.deps import get_model_service
from modelops.api.model_service import ModelNotReadyError, ModelService
from modelops.api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    ReadyResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()
ModelServiceDep = Annotated[ModelService, Depends(get_model_service)]


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    """Liveness: the process is up. Does not require a loaded model."""
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse}},
    tags=["ops"],
)
def ready(service: ModelServiceDep) -> ReadyResponse:
    """Readiness: an approved model is loaded and predictions can be served."""
    if not service.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "model_loaded": False,
                "detail": service.load_error or "model_not_loaded",
            },
        )
    return ReadyResponse(status="ready", model_loaded=True, detail=None)


@router.get("/model-info", response_model=ModelInfoResponse, tags=["model"])
def model_info(service: ModelServiceDep) -> ModelInfoResponse:
    """Safe model metadata for operators and clients (no secrets / raw paths abuse)."""
    info = service.info()
    # Expose basename only to avoid leaking full local user paths in demos.
    raw_path = info.get("model_path")
    safe_path = Path(raw_path).name if isinstance(raw_path, str) and raw_path else None

    return ModelInfoResponse(
        ready=bool(info["ready"]),
        model_path=safe_path,
        model_type=info.get("model_type"),
        target=info.get("target"),
        features=list(info.get("features") or []),
        scenario=info.get("scenario"),
        trained_at_utc=info.get("trained_at_utc"),
        dataset_year=info.get("dataset_year"),
        dataset_month=info.get("dataset_month"),
        metrics=info.get("metrics"),
        detail=info.get("detail"),
    )


@router.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        422: {"description": "Validation error"},
        503: {"description": "Model not ready"},
    },
    tags=["prediction"],
)
def predict(
    body: PredictRequest,
    service: ModelServiceDep,
) -> PredictResponse:
    """Score one pre-trip feature vector. Never trains."""
    try:
        value = service.predict_one(body.as_feature_frame_dict())
    except ModelNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready to serve predictions",
        ) from exc
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed",
        ) from None

    info = service.info()
    model_id = None
    if info.get("trained_at_utc"):
        model_id = f"baseline-{info.get('dataset_year')}-{info.get('dataset_month')}"

    return PredictResponse(
        prediction=round(value, 4),
        model_id=model_id,
    )
