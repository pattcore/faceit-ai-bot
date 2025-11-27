"""
Rate Limiter Middleware
Request rate limiting
"""
import time
import logging
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from collections import defaultdict
from prometheus_client import Counter
from ..services.cache_service import cache_service
from ..auth.security import decode_access_token
from ..config.settings import settings

logger = logging.getLogger(__name__)


RATE_LIMIT_VIOLATIONS_TOTAL = Counter(
    "rate_limit_violations_total",
    "Total number of rate limit violations",
    ["scope", "limit_type"],
)


RATE_LIMIT_BANS_TOTAL = Counter(
    "rate_limit_bans_total",
    "Total number of rate limit autobans",
    ["scope"],
)


class RateLimiter:
    """Rate limiter for API protection"""

    def __init__(
        self,
        requests_per_minute: int = settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        requests_per_hour: int = settings.RATE_LIMIT_REQUESTS_PER_HOUR,
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

    def _get_rate_identity(self, request: Request) -> Tuple[str, str | None]:
        """Get rate limiting identity (IP and optional user id)"""
        client_ip = self._get_client_ip(request)

        user_id: str | None = None
        auth_header = request.headers.get("Authorization") or ""
        token = None

        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        if not token:
            token = request.cookies.get("access_token")

        if token:
            payload = decode_access_token(token)
            if payload:
                sub = payload.get("sub")
                if sub is not None:
                    user_id = str(sub)

        return client_ip, user_id

    async def _log_limit_exceeded(
        self,
        request: Request,
        client_ip: str,
        user_id: str | None,
        minute_count: int,
        hour_count: int,
        limit_type: str,
    ) -> None:
        """Log detailed information about a rate limit violation"""
        scope = "ip_and_user" if user_id is not None else "ip"
        try:
            RATE_LIMIT_VIOLATIONS_TOTAL.labels(
                scope=scope,
                limit_type=limit_type,
            ).inc()
        except Exception:
            logger.exception("Failed to increment rate limit violation metric")

        logger.warning(
            "Rate limit exceeded: ip=%s user_id=%s method=%s path=%s minute_count=%s hour_count=%s limit_type=%s",
            client_ip,
            user_id,
            request.method,
            request.url.path,
            minute_count,
            hour_count,
            limit_type,
        )

    async def _check_ban(self, client_ip: str, user_id: str | None) -> Tuple[bool, str | None]:
        """Check if IP or user is temporarily banned due to rate limit violations"""
        if self.redis_client is None or not settings.RATE_LIMIT_BAN_ENABLED:
            return False, None

        try:
            ban_keys: list[Tuple[str, str]] = [(f"rate:ban:ip:{client_ip}", "ip")]
            if user_id is not None:
                ban_keys.append((f"rate:ban:user:{user_id}", "user"))

            for key, label in ban_keys:
                exists = await self.redis_client.exists(key)
                if exists:
                    ttl = await self.redis_client.ttl(key)
                    logger.warning(
                        "Rate limit ban active for %s=%s ttl=%s",
                        label,
                        client_ip if label == "ip" else user_id,
                        ttl,
                    )
                    return True, "Too many requests, access temporarily blocked"
        except Exception as e:
            logger.error("Rate limit ban check error: %s", e)

        return False, None

    async def _register_violation_and_maybe_ban(
        self,
        client_ip: str,
        user_id: str | None,
    ) -> None:
        """Increase violation counters and apply temporary ban if threshold exceeded"""
        if self.redis_client is None or not settings.RATE_LIMIT_BAN_ENABLED:
            return

        try:
            max_count = 0

            ip_key = f"rate:viol:ip:{client_ip}"
            ip_count = await self.redis_client.incr(ip_key)
            if ip_count == 1:
                await self.redis_client.expire(ip_key, settings.RATE_LIMIT_BAN_WINDOW_SECONDS)
            max_count = max(max_count, ip_count)

            user_key = None
            user_count = None
            if user_id is not None:
                user_key = f"rate:viol:user:{user_id}"
                user_count = await self.redis_client.incr(user_key)
                if user_count == 1:
                    await self.redis_client.expire(user_key, settings.RATE_LIMIT_BAN_WINDOW_SECONDS)
                max_count = max(max_count, user_count)

            if max_count >= settings.RATE_LIMIT_BAN_THRESHOLD:
                ban_ttl = settings.RATE_LIMIT_BAN_TTL_SECONDS
                await self.redis_client.setex(f"rate:ban:ip:{client_ip}", ban_ttl, "1")
                if user_id is not None:
                    await self.redis_client.setex(f"rate:ban:user:{user_id}", ban_ttl, "1")
                logger.warning(
                    "Rate limit autoban applied: ip=%s user_id=%s violations=%s",
                    client_ip,
                    user_id,
                    max_count,
                )

                scope = "ip_and_user" if user_id is not None else "ip"
                try:
                    RATE_LIMIT_BANS_TOTAL.labels(scope=scope).inc()
                except Exception:
                    logger.exception("Failed to increment rate limit ban metric")
        except Exception as e:
            logger.error("Rate limit violation registration error: %s", e)

    async def check_rate_limit(self, request: Request) -> Tuple[bool, str]:
        """
        Check rate limit

        Returns:
            (allowed, message)
        """
        client_ip, user_id = self._get_rate_identity(request)
        current_time = time.time()

        bypass_user_id = getattr(settings, "RATE_LIMIT_BYPASS_USER_ID", None)
        if user_id is not None and bypass_user_id is not None and str(user_id) == str(bypass_user_id):
            return True, "OK"

        if self.redis_client is not None:
            # Check active ban first
            banned, ban_message = await self._check_ban(client_ip, user_id)
            if banned:
                return False, ban_message or "Too many requests"

            try:
                minute_key_ip = f"rate:ip:{client_ip}:minute"
                hour_key_ip = f"rate:ip:{client_ip}:hour"

                minute_count_ip = await self.redis_client.incr(minute_key_ip)
                if minute_count_ip == 1:
                    await self.redis_client.expire(minute_key_ip, 60)

                hour_count_ip = await self.redis_client.incr(hour_key_ip)
                if hour_count_ip == 1:
                    await self.redis_client.expire(hour_key_ip, 3600)

                minute_count = minute_count_ip
                hour_count = hour_count_ip

                if user_id is not None:
                    minute_key_user = f"rate:user:{user_id}:minute"
                    hour_key_user = f"rate:user:{user_id}:hour"

                    minute_count_user = await self.redis_client.incr(minute_key_user)
                    if minute_count_user == 1:
                        await self.redis_client.expire(minute_key_user, 60)

                    hour_count_user = await self.redis_client.incr(hour_key_user)
                    if hour_count_user == 1:
                        await self.redis_client.expire(hour_key_user, 3600)

                    minute_count = max(minute_count_ip, minute_count_user)
                    hour_count = max(hour_count_ip, hour_count_user)

                if minute_count > self.requests_per_minute or hour_count > self.requests_per_hour:
                    limit_type = (
                        "minute" if minute_count > self.requests_per_minute else "hour"
                    )
                    await self._log_limit_exceeded(
                        request,
                        client_ip,
                        user_id,
                        minute_count,
                        hour_count,
                        limit_type,
                    )
                    await self._register_violation_and_maybe_ban(client_ip, user_id)

                    if minute_count > self.requests_per_minute:
                        return (
                            False,
                            f"Rate limit exceeded: "
                            f"{self.requests_per_minute} requests per minute",
                        )

                    return (
                        False,
                        f"Rate limit exceeded: "
                        f"{self.requests_per_hour} requests per hour",
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
        if minute_count >= self.requests_per_minute or hour_count >= self.requests_per_hour:
            limit_type = (
                "minute" if minute_count >= self.requests_per_minute else "hour"
            )
            await self._log_limit_exceeded(
                request,
                client_ip,
                user_id,
                minute_count,
                hour_count,
                limit_type,
            )

            if minute_count >= self.requests_per_minute:
                return (
                    False,
                    f"Rate limit exceeded: "
                    f"{self.requests_per_minute} requests per minute",
                )

            return (
                False,
                f"Rate limit exceeded: "
                f"{self.requests_per_hour} requests per hour",
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
rate_limiter = RateLimiter()
