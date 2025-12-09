"""Middleware for structured logging of HTTP requests and responses."""

import time
import logging

from fastapi import Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.structured_logging import request_logger

logger = logging.getLogger(__name__)


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status"],
)


HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


API_ERRORS_TOTAL = Counter(
    "api_errors_total",
    "Total API error responses (4xx and 5xx)",
    ["route", "status"],
)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses with structlog."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response."""
        start_time = time.time()

        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)

        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        request_logger.log_request(
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
            user_id=user_id,
        )

        try:
            response = await call_next(request)
            duration_seconds = time.time() - start_time
            duration_ms = duration_seconds * 1000

            request_logger.log_response(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
            )

            try:
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    route=route_path,
                    status=str(response.status_code),
                ).inc()
                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=request.method,
                    route=route_path,
                ).observe(duration_seconds)
                if 400 <= response.status_code < 600:
                    API_ERRORS_TOTAL.labels(
                        route=route_path,
                        status=str(response.status_code),
                    ).inc()
            except Exception:
                logger.exception("Failed to update HTTP Prometheus metrics")

            return response

        except Exception as exc:
            duration_seconds = time.time() - start_time
            duration_ms = duration_seconds * 1000

            request_logger.log_error(
                method=request.method,
                path=request.url.path,
                error=exc,
                user_id=user_id,
            )

            try:
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    route=route_path,
                    status="500",
                ).inc()
                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=request.method,
                    route=route_path,
                ).observe(duration_seconds)
                API_ERRORS_TOTAL.labels(
                    route=route_path,
                    status="500",
                ).inc()
            except Exception:
                logger.exception("Failed to update HTTP Prometheus metrics on error")

            raise
