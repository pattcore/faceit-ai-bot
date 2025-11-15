"""Performance optimization utilities for caching and query optimization."""

import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

import redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis caching for application data."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")

        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
    ) -> bool:
        """Set value in cache with TTL."""
        if not self.redis_client:
            return False

        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str),
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {str(e)}")
            return 0


# Global cache manager instance
cache_manager = CacheManager()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            result = func(*args, **kwargs)

            if result is not None:
                cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class QueryOptimizer:
    """Utilities for optimizing SQLAlchemy queries."""

    @staticmethod
    def get_user_with_relations(db: Session, user_id: int):
        """Get user with all related data in single query."""
        from ..database.models import User

        return (
            db.query(User)
            .filter(User.id == user_id)
            .outerjoin(User.subscription)
            .outerjoin(User.payments)
        ).first()

    @staticmethod
    def get_users_batch(db: Session, user_ids: list):
        """Get multiple users efficiently."""
        from ..database.models import User

        return (
            db.query(User)
            .filter(User.id.in_(user_ids))
            .all()
        )

    @staticmethod
    def get_active_subscriptions(db: Session):
        """Get all active subscriptions with user data."""
        from ..database.models import Subscription, User

        return (
            db.query(Subscription)
            .join(User)
            .filter(Subscription.is_active is True)
            .all()
        )


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all cache entries for a user."""
    cache_manager.clear_pattern(f"*user:{user_id}*")
    logger.info(f"Invalidated cache for user {user_id}")


def invalidate_subscription_cache(user_id: int) -> None:
    """Invalidate subscription cache for a user."""
    cache_manager.clear_pattern(f"*subscription:*user:{user_id}*")
    logger.info(f"Invalidated subscription cache for user {user_id}")
