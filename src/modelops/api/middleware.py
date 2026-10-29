"""HTTP middleware for metrics and structured request logging."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match

from modelops.api.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger("modelops.api")


def _route_template(request: Request) -> str:
    """Use the matched route path template (low cardinality), not the raw URL."""
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL and hasattr(route, "path"):
            return str(route.path)
    return "unmatched"


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        handler = _route_template(request)
        method = request.method
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            elapsed = time.perf_counter() - started
            REQUEST_LATENCY.labels(method=method, handler=handler).observe(elapsed)
            REQUEST_COUNT.labels(
                method=method,
                handler=handler,
                status_code=str(status_code),
            ).inc()
            # Structured-ish log line without request body / feature payloads.
            logger.info(
                "request method=%s handler=%s status=%s duration_ms=%.2f",
                method,
                handler,
                status_code,
                elapsed * 1000.0,
            )
