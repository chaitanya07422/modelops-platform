"""FastAPI inference service for approved ModelOps models."""

from modelops.api.app import create_app

__all__ = ["create_app"]
