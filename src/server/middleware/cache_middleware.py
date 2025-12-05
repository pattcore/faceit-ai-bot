"""Redis caching middleware for FastAPI"""

import json
import hashlib
import os
from urllib.parse import urlparse

import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def _get_redis_config():
    """Parse Redis URL from environment.

    Supports formats:
    - redis://localhost:6379
    - redis://:password@host:port
    - redis://host
    """

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    parsed = urlparse(redis_url)

    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    password = parsed.password

    return host, port, password


# Redis connection
host, port, password = _get_redis_config()
redis_client = redis.Redis(
    host=host,
    port=port,
    password=password,
    decode_responses=True,
)


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching GET requests"""

    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl

    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Skip caching for auth endpoints and health checks
        if any(path in str(request.url.path) for path in ["/auth", "/health", "/metrics", "/docs"]):
            return await call_next(request)

        # Create cache key from URL and query params
        cache_key = self._generate_cache_key(request)

        try:
            # Try to get from cache
            cached_response = redis_client.get(cache_key)
            if cached_response:
                # Parse cached response
                cached_data = json.loads(cached_response)
                # Copy headers and drop Content-Length so it can be recalculated
                headers = dict(cached_data["headers"])
                headers.pop("content-length", None)
                response = Response(
                    content=json.dumps(cached_data["content"]),
                    status_code=cached_data["status_code"],
                    headers=headers,
                )
                response.headers["X-Cache"] = "HIT"
                return response

        except Exception:
            # If Redis fails, continue without caching
            pass

        # Get response from handler
        response = await call_next(request)

        # Cache successful GET responses
        if response.status_code == 200:
            try:
                content = b""
                async for chunk in response.body_iterator:
                    content += chunk

                # Create cache data
                cache_data = {
                    "content": json.loads(content.decode()),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }

                # Store in cache
                redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Return response with cache header
                headers = dict(response.headers)
                headers["X-Cache"] = "MISS"
                # Remove Content-Length so Starlette will recalculate it
                headers.pop("content-length", None)
                return Response(
                    content=json.dumps(cache_data["content"]),
                    status_code=response.status_code,
                    headers=headers,
                )

            except Exception:
                # If caching fails, return original response
                response.headers["X-Cache"] = "ERROR"
                return response

        return response

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        url = str(request.url)
        query_params = str(request.query_params)

        # Include a user-specific component so cached responses are not shared
        # across different authenticated users.
        auth_header = request.headers.get("Authorization") or ""
        user_token = ""

        if auth_header.lower().startswith("bearer "):
            user_token = auth_header.split(" ", 1)[1].strip()

        if not user_token:
            cookie_token = request.cookies.get("access_token")
            if cookie_token:
                user_token = cookie_token

        user_token_hash = ""
        if user_token:
            user_token_hash = hashlib.sha256(user_token.encode()).hexdigest()

        # Create hash of URL + query params + user identity (if any)
        key_data = f"{url}:{query_params}:{user_token_hash}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()

        return f"api_cache:{key_hash}"


# Cache invalidation functions
def invalidate_cache(pattern: str = "*"):
    """Invalidate cache keys matching pattern"""
    try:
        keys = redis_client.keys(f"api_cache:{pattern}")
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass


def invalidate_user_cache(user_id: str):
    """Invalidate cache for specific user"""
    invalidate_cache(f"*{user_id}*")


def clear_all_cache():
    """Clear all cached data"""
    try:
        keys = redis_client.keys("api_cache:*")
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass
