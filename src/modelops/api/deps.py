"""Shared FastAPI dependencies."""

from __future__ import annotations

from modelops.api.model_service import ModelService

# Process-wide service mutated during app lifespan / tests.
model_service = ModelService()


def get_model_service() -> ModelService:
    return model_service
