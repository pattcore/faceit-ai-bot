"""Security middleware for basic security headers.

Rate limiting via slowapi is disabled in the production image because
the dependency is not installed. This middleware only manages security headers.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware with basic protection headers."""

    async def dispatch(self, request: Request, call_next):
        # Basic security headers
        response = await call_next(request)

        path = request.url.path
        sensitive_prefixes = (
            "/auth",
            "/admin",
            "/payments",
            "/subscriptions",
            "/dashboard",
        )
        if path.startswith(sensitive_prefixes):
            if "X-Robots-Tag" not in response.headers:
                response.headers["X-Robots-Tag"] = "noindex, nofollow, nosnippet"

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        if "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"] = csp

        if "Permissions-Policy" not in response.headers:
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), fullscreen=(self), "
                "payment=(), usb=(), accelerometer=(), gyroscope=(), magnetometer=()"
            )

        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]

        return response
