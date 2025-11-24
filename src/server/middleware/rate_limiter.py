"""
Rate Limiter Middleware
Request rate limiting
"""
import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from collections import defaultdict
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API protection"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        self.redis_client = (
            cache_service.redis_client if getattr(cache_service, "enabled", False) else None
        )

        # Request storage: {ip: [(timestamp, count)]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)

    def _clean_old_requests(
        self,
        requests_list: list,
        time_window: int
    ) -> list:
        """Clean old requests"""
        current_time = time.time()
        return [
            (timestamp, count)
            for timestamp, count in requests_list
            if current_time - timestamp < time_window
        ]

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP"""
        # Check proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct IP
        if request.client:
            return request.client.host

        return "unknown"

    async def check_rate_limit(self, request: Request) -> Tuple[bool, str]:
        """
        Check rate limit

        Returns:
            (allowed, message)
        """
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        if self.redis_client is not None:
            try:
                minute_key = f"rate:ip:{client_ip}:minute"
                hour_key = f"rate:ip:{client_ip}:hour"

                minute_count = await self.redis_client.incr(minute_key)
                if minute_count == 1:
                    await self.redis_client.expire(minute_key, 60)

                hour_count = await self.redis_client.incr(hour_key)
                if hour_count == 1:
                    await self.redis_client.expire(hour_key, 3600)

                if minute_count > self.requests_per_minute:
                    return (
                        False,
                        f"Rate limit exceeded: "
                        f"{self.requests_per_minute} requests per minute"
                    )

                if hour_count > self.requests_per_hour:
                    return (
                        False,
                        f"Rate limit exceeded: "
                        f"{self.requests_per_hour} requests per hour"
                    )

                return True, "OK"
            except Exception as e:
                logger.error(f"Redis rate limit error: {e}")
                self.redis_client = None

        # Clean old requests
        self.minute_requests[client_ip] = (
            self._clean_old_requests(
                self.minute_requests[client_ip],
                60  # 1 minute
            )
        )
        self.hour_requests[client_ip] = (
            self._clean_old_requests(
                self.hour_requests[client_ip],
                3600  # 1 hour
            )
        )

        # Count requests
        minute_count = sum(
            count
            for _, count in self.minute_requests[client_ip]
        )
        hour_count = sum(
            count
            for _, count in self.hour_requests[client_ip]
        )

        # Check limits
        if minute_count >= self.requests_per_minute:
            return (
                False,
                f"Rate limit exceeded: "
                f"{self.requests_per_minute} requests per minute"
            )

        if hour_count >= self.requests_per_hour:
            return (
                False,
                f"Rate limit exceeded: "
                f"{self.requests_per_hour} requests per hour"
            )

        # Add current request
        self.minute_requests[client_ip].append((current_time, 1))
        self.hour_requests[client_ip].append((current_time, 1))

        return True, "OK"

    async def __call__(self, request: Request):
        """Middleware for FastAPI"""
        allowed, message = await self.check_rate_limit(request)

        if not allowed:
            client = self._get_client_ip(request)
            logger.warning(
                f"Rate limit exceeded for {client}"
            )
            raise HTTPException(
                status_code=429,
                detail=message
            )


# Singleton instance
rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000
)
