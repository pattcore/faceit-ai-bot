"""Middleware for structured logging of HTTP requests and responses."""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.structured_logging import request_logger

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses with structlog."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response."""
        start_time = time.time()

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
            duration_ms = (time.time() - start_time) * 1000

            request_logger.log_response(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
            )

            return response

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000

            request_logger.log_error(
                method=request.method,
                path=request.url.path,
                error=exc,
                user_id=user_id,
            )

            raise
