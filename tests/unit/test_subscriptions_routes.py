"""Unit tests for subscriptions routes (/subscriptions)."""

from datetime import datetime, timedelta
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.server.features.subscriptions.routes import router, subscription_service
from src.server.features.subscriptions.models import (
    Subscription,
    SubscriptionFeatures,
    SubscriptionTier,
    UserSubscription,
)


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def _make_plan(tier: SubscriptionTier, price: float = 9.99) -> Subscription:
    return Subscription(
        tier=tier,
        price=price,
        currency="USD",
        features=SubscriptionFeatures(
            demos_per_month=5,
            detailed_analysis=True,
            teammate_search=True,
            custom_recommendations=True,
            priority_support=False,
            ai_coach=False,
            team_analysis=False,
        ),
        description="Test plan",
    )


@pytest.mark.asyncio
async def test_get_subscription_plans_route_uses_service(monkeypatch, client):
    plans = {
        SubscriptionTier.FREE.value: _make_plan(SubscriptionTier.FREE),
        SubscriptionTier.BASIC.value: _make_plan(SubscriptionTier.BASIC),
    }

    async def fake_get_plans():  # noqa: D401
        return plans

    monkeypatch.setattr(subscription_service, "get_subscription_plans", fake_get_plans)

    response = client.get("/subscriptions/plans")

    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {SubscriptionTier.FREE.value, SubscriptionTier.BASIC.value}
    assert data[SubscriptionTier.FREE.value]["tier"] == SubscriptionTier.FREE.value


@pytest.mark.asyncio
async def test_get_user_subscription_route_returns_subscription(monkeypatch, client):
    now = datetime.utcnow()
    subscription = UserSubscription(
        user_id="user-1",
        subscription_tier=SubscriptionTier.PRO,
        start_date=now,
        end_date=now + timedelta(days=30),
        is_active=True,
        demos_remaining=10,
    )

    async def fake_get_user_subscription(user_id: str):  # noqa: ARG001
        return subscription

    monkeypatch.setattr(
        subscription_service,
        "get_user_subscription",
        fake_get_user_subscription,
    )

    response = client.get("/subscriptions/user-1")

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "user-1"
    assert body["subscription_tier"] == SubscriptionTier.PRO.value


@pytest.mark.asyncio
async def test_get_user_subscription_route_none_returns_null(monkeypatch, client):
    async def fake_get_user_subscription(user_id: str):  # noqa: ARG001
        return None

    monkeypatch.setattr(
        subscription_service,
        "get_user_subscription",
        fake_get_user_subscription,
    )

    response = client.get("/subscriptions/no-sub")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_create_subscription_route_calls_service(monkeypatch, client):
    now = datetime.utcnow()
    created = UserSubscription(
        user_id="user-2",
        subscription_tier=SubscriptionTier.BASIC,
        start_date=now,
        end_date=now + timedelta(days=30),
        is_active=True,
        demos_remaining=5,
    )

    calls: list[tuple[str, SubscriptionTier]] = []

    async def fake_create_subscription(user_id: str, tier: SubscriptionTier):
        calls.append((user_id, tier))
        return created

    monkeypatch.setattr(
        subscription_service,
        "create_subscription",
        fake_create_subscription,
    )

    response = client.post("/subscriptions/user-2", params={"tier": "basic"})

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "user-2"
    assert body["subscription_tier"] == SubscriptionTier.BASIC.value
    assert calls == [("user-2", SubscriptionTier.BASIC)]


@pytest.mark.asyncio
async def test_check_feature_access_route_returns_flag(monkeypatch, client):
    calls: list[tuple[str, str]] = []

    async def fake_check_feature_access(user_id: str, feature: str):
        calls.append((user_id, feature))
        return True

    monkeypatch.setattr(
        subscription_service,
        "check_feature_access",
        fake_check_feature_access,
    )

    response = client.get(
        "/subscriptions/user-3/check-feature",
        params={"feature": "ai_coach"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {"has_access": True}
    assert calls == [("user-3", "ai_coach")]
