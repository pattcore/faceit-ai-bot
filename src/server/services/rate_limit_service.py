import logging
from datetime import datetime
from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .cache_service import cache_service
from ..config.settings import settings
from ..database.models import Subscription, SubscriptionTier
from ..metrics_business import RATE_LIMIT_EXCEEDED


logger = logging.getLogger(__name__)


class RateLimitService:
    """Per-user operation rate limiting based on subscription tier.

    Uses Redis (via cache_service) to store counters per user and operation.
    Fallback: if Redis is not available, limits are not enforced here
    (only global IP/user limits in middleware remain).
    """

    def __init__(self) -> None:
        self.redis_client = (
            cache_service.redis_client
            if getattr(cache_service, "enabled", False)
            else None
        )

        # Per-operation limits per subscription tier.
        # Values are chosen to be sufficient for users and safe for the server.
        # per_min: maximum operations per minute
        # per_day: maximum operations per day
        self.operation_limits: Dict[str, Dict[str, Dict[str, int]]] = {
            "demo_analyze": {
                "free": {"per_min": 1, "per_day": 5},
                "basic": {"per_min": 1, "per_day": 20},
                "pro": {"per_min": 2, "per_day": 50},
                "elite": {"per_min": 3, "per_day": 200},
            },
            "player_analysis": {
                "free": {"per_min": 1, "per_day": 10},
                "basic": {"per_min": 2, "per_day": 50},
                "pro": {"per_min": 5, "per_day": 200},
                "elite": {"per_min": 10, "per_day": 1000},
            },
            "teammates_search": {
                "free": {"per_min": 2, "per_day": 20},
                "basic": {"per_min": 5, "per_day": 100},
                "pro": {"per_min": 10, "per_day": 300},
                "elite": {"per_min": 20, "per_day": 1000},
            },
        }

    async def enforce_user_operation_limit(
        self,
        db: Session,
        user_id: int,
        operation: str,
    ) -> None:
        """Enforce per-user operation limit based on subscription tier.

        Raises HTTPException(429) when limit is exceeded.
        """
        bypass_user_id = getattr(settings, "RATE_LIMIT_BYPASS_USER_ID", None)
        if bypass_user_id is not None and str(user_id) == str(bypass_user_id):
            return

        if self.redis_client is None:
            return

        op_limits = self.operation_limits.get(operation)
        if not op_limits:
            return

        tier_key = await self._get_user_tier_key(db, user_id)
        limits = op_limits.get(tier_key) or op_limits.get("free")
        if not limits:
            return

        now = datetime.utcnow()

        # Per-minute limit
        per_min = limits.get("per_min") or 0
        if per_min > 0:
            minute_key = f"rl:op:{operation}:user:{user_id}:minute"
            try:
                minute_count = await self.redis_client.incr(minute_key)
                if minute_count == 1:
                    await self.redis_client.expire(minute_key, 60)
                if minute_count > per_min:
                    try:
                        RATE_LIMIT_EXCEEDED.labels(
                            operation=operation,
                            tier=tier_key,
                            window="minute",
                        ).inc()
                    except Exception:
                        # Metrics must not affect rate limiting behavior
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=(
                            "Превышен лимит запросов для этой операции. "
                            "Попробуйте позже."
                        ),
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Rate limit (minute) error: %s", e)

        # Per-day limit
        per_day = limits.get("per_day") or 0
        if per_day > 0:
            day_suffix = now.strftime("%Y%m%d")
            day_key = f"rl:op:{operation}:user:{user_id}:day:{day_suffix}"
            try:
                day_count = await self.redis_client.incr(day_key)
                if day_count == 1:
                    await self.redis_client.expire(day_key, 86400)
                if day_count > per_day:
                    try:
                        RATE_LIMIT_EXCEEDED.labels(
                            operation=operation,
                            tier=tier_key,
                            window="day",
                        ).inc()
                    except Exception:
                        # Metrics must not affect rate limiting behavior
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=(
                            "Достигнут дневной лимит для этой операции "
                            "на вашем тарифе. Попробуйте завтра или обновите подписку."
                        ),
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Rate limit (day) error: %s", e)

    async def _get_user_tier_key(self, db: Session, user_id: int) -> str:
        """Get user's subscription tier as lower-case key (free/basic/pro/elite)."""
        tier: Optional[SubscriptionTier] = None

        try:
            subscription: Optional[Subscription] = (
                db.query(Subscription)
                .filter(Subscription.user_id == user_id, Subscription.is_active == True)
                .order_by(Subscription.expires_at.desc())
                .first()
            )
        except Exception as e:
            logger.error("Failed to load subscription for rate limiting: %s", e)
            subscription = None

        now = datetime.utcnow()

        if (
            subscription
            and subscription.expires_at is not None
            and subscription.expires_at < now
        ):
            subscription = None

        if subscription is not None:
            value = subscription.tier
            if isinstance(value, SubscriptionTier):
                tier = value
            else:
                try:
                    tier = SubscriptionTier(value)
                except Exception:
                    tier = SubscriptionTier.FREE
        else:
            tier = SubscriptionTier.FREE

        return tier.value.lower()


rate_limit_service = RateLimitService()
