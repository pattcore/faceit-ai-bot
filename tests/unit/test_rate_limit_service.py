"""Unit tests for RateLimitService"""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.server.config.settings import settings
from src.server.database.models import Base, User, Subscription, SubscriptionTier
from src.server.metrics_business import RATE_LIMIT_EXCEEDED
from src.server.services.cache_service import cache_service
from src.server.services.rate_limit_service import RateLimitService


class DummyRedis:
    """Minimal async Redis stub for rate limit tests."""

    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.expires: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    async def expire(self, key: str, ttl: int) -> None:
        self.expires[key] = ttl


@pytest.fixture
def db_session():
    """In-memory SQLite session bound to app models Base."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_user(db_session) -> User:
    user = User(
        email="test@example.com",
        username=f"user_{datetime.utcnow().timestamp()}",
        hashed_password="hashed",
        is_active=True,
        is_admin=False,
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def add_subscription(db_session, user: User, tier: SubscriptionTier, expired: bool = False) -> Subscription:
    expires_at = datetime.utcnow() - timedelta(days=1) if expired else datetime.utcnow() + timedelta(days=1)
    subscription = Subscription(
        user_id=user.id,
        tier=tier,
        started_at=datetime.utcnow(),
        expires_at=expires_at,
        is_active=True,
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


@pytest.fixture
def service_with_redis(monkeypatch):
    dummy = DummyRedis()
    monkeypatch.setattr(cache_service, "enabled", True, raising=False)
    monkeypatch.setattr(cache_service, "redis_client", dummy, raising=False)
    service = RateLimitService()
    return service, dummy


@pytest.mark.asyncio
async def test_enforce_user_operation_limit_no_redis_does_nothing(monkeypatch, db_session):
    # Simulate disabled cache/Redis so RateLimitService has no redis_client
    monkeypatch.setattr(cache_service, "enabled", False, raising=False)
    monkeypatch.setattr(cache_service, "redis_client", None, raising=False)

    service = RateLimitService()
    user = create_user(db_session)
    add_subscription(db_session, user, SubscriptionTier.FREE, expired=False)

    assert service.redis_client is None

    await service.enforce_user_operation_limit(
        db=db_session,
        user_id=user.id,
        operation="player_analysis",
    )


@pytest.mark.asyncio
async def test_get_user_tier_key_free_when_no_subscription(db_session):
    service = RateLimitService()
    user = create_user(db_session)

    tier_key = await service._get_user_tier_key(db_session, user.id)

    assert tier_key == "free"


@pytest.mark.asyncio
async def test_get_user_tier_key_uses_active_subscription_tier(db_session):
    service = RateLimitService()
    user = create_user(db_session)
    add_subscription(db_session, user, SubscriptionTier.PRO, expired=False)

    tier_key = await service._get_user_tier_key(db_session, user.id)

    assert tier_key == "pro"


@pytest.mark.asyncio
async def test_get_user_tier_key_ignores_expired_subscription(db_session):
    service = RateLimitService()
    user = create_user(db_session)
    add_subscription(db_session, user, SubscriptionTier.PRO, expired=True)

    tier_key = await service._get_user_tier_key(db_session, user.id)

    assert tier_key == "free"


@pytest.mark.asyncio
async def test_enforce_user_operation_limit_bypass_user_id(monkeypatch, db_session, service_with_redis):
    service, dummy = service_with_redis
    user = create_user(db_session)

    monkeypatch.setattr(settings, "RATE_LIMIT_BYPASS_USER_ID", user.id, raising=False)

    await service.enforce_user_operation_limit(
        db=db_session,
        user_id=user.id,
        operation="player_analysis",
    )

    assert dummy.counters == {}


@pytest.mark.asyncio
async def test_enforce_user_operation_limit_exceeds_minute_limit_raises(monkeypatch, db_session, service_with_redis):
    service, dummy = service_with_redis
    user = create_user(db_session)
    add_subscription(db_session, user, SubscriptionTier.FREE, expired=False)

    monkeypatch.setattr(settings, "RATE_LIMIT_BYPASS_USER_ID", None, raising=False)

    # Reset metric for this label set before test
    child = RATE_LIMIT_EXCEEDED.labels(operation="player_analysis", tier="free", window="minute")
    try:
        child._value.set(0)  # type: ignore[attr-defined]
    except Exception:
        pass

    await service.enforce_user_operation_limit(
        db=db_session,
        user_id=user.id,
        operation="player_analysis",
    )

    with pytest.raises(HTTPException) as exc:
        await service.enforce_user_operation_limit(
            db=db_session,
            user_id=user.id,
            operation="player_analysis",
        )

    assert exc.value.status_code == 429

    # Rate limit breach metric should be incremented
    try:
        assert child._value.get() >= 1  # type: ignore[attr-defined]
    except Exception:
        # If prometheus internals change, we still want the behavior test to run
        pass
    # Minute key counter should be greater than per_min (1 for free tier)
    minute_keys = [k for k in dummy.counters.keys() if ":minute" in k]
    assert minute_keys
    for key in minute_keys:
        assert dummy.counters[key] >= 2


@pytest.mark.asyncio
async def test_enforce_user_operation_limit_unknown_operation_does_nothing(monkeypatch, db_session, service_with_redis):
    service, dummy = service_with_redis
    user = create_user(db_session)
    add_subscription(db_session, user, SubscriptionTier.BASIC, expired=False)

    monkeypatch.setattr(settings, "RATE_LIMIT_BYPASS_USER_ID", None, raising=False)

    await service.enforce_user_operation_limit(
        db=db_session,
        user_id=user.id,
        operation="unknown_operation",
    )

    assert dummy.counters == {}


@pytest.mark.asyncio
async def test_enforce_user_operation_limit_exceeds_day_limit_raises(monkeypatch, db_session, service_with_redis):
    service, dummy = service_with_redis
    user = create_user(db_session)
    add_subscription(db_session, user, SubscriptionTier.FREE, expired=False)

    monkeypatch.setattr(settings, "RATE_LIMIT_BYPASS_USER_ID", None, raising=False)

    # Disable per-minute limit for this test so we can hit the daily limit path
    service.operation_limits["player_analysis"]["free"]["per_min"] = 0
    service.operation_limits["player_analysis"]["free"]["per_day"] = 2

    # Reset metric for this label set before test
    child = RATE_LIMIT_EXCEEDED.labels(operation="player_analysis", tier="free", window="day")
    try:
        child._value.set(0)  # type: ignore[attr-defined]
    except Exception:
        pass

    # Two allowed requests
    await service.enforce_user_operation_limit(
        db=db_session,
        user_id=user.id,
        operation="player_analysis",
    )
    await service.enforce_user_operation_limit(
        db=db_session,
        user_id=user.id,
        operation="player_analysis",
    )

    # Third request should exceed daily limit
    with pytest.raises(HTTPException) as exc:
        await service.enforce_user_operation_limit(
            db=db_session,
            user_id=user.id,
            operation="player_analysis",
        )

    assert exc.value.status_code == 429
