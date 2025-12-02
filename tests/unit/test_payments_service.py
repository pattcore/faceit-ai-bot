"""Unit tests for PaymentService"""

import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi import HTTPException

from src.server.features.payments.models import (
    PaymentRequest,
    PaymentProvider,
    PaymentMethod,
    Currency,
)
from src.server.features.payments.service import PaymentService
from src.server.database.models import (
    Base,
    Payment as DBPayment,
    PaymentStatus as DBPaymentStatus,
    Subscription as DBSubscription,
    SubscriptionTier as DBSubscriptionTier,
)


class DummySettings(SimpleNamespace):
    """Minimal settings stub for PaymentService tests."""


@pytest.fixture
def settings_stub():
    return DummySettings(
        WEBSITE_URL="http://localhost:3000",
        API_URL="http://localhost:8000",
        SBP_API_URL=None,
        SBP_TOKEN=None,
        YOOKASSA_SHOP_ID=None,
        YOOKASSA_SECRET_KEY=None,
        YOOKASSA_API_URL="https://api.yookassa.ru/v3/payments",
    )


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


@pytest.mark.asyncio
async def test_create_payment_sbp_mock_when_not_configured(settings_stub):
    service = PaymentService(settings_stub)

    request = PaymentRequest(
        subscription_tier="basic",
        amount=100.0,
        currency=Currency.RUB,
        payment_method=PaymentMethod.SBP,
        provider=PaymentProvider.SBP,
        description="Test payment",
        user_id="1",
    )

    response = await service.create_payment(request)

    assert response.status == "pending"
    assert response.amount == pytest.approx(100.0)
    assert response.currency == Currency.RUB
    assert "payment/success" in response.payment_url


@pytest.mark.asyncio
async def test_create_payment_yookassa_mock_when_not_configured(settings_stub):
    service = PaymentService(settings_stub)

    request = PaymentRequest(
        subscription_tier="basic",
        amount=150.0,
        currency=Currency.RUB,
        payment_method=PaymentMethod.BANK_CARD,
        provider=PaymentProvider.YOOKASSA,
        description="Test payment",
        user_id="1",
    )

    response = await service.create_payment(request)

    assert response.status == "pending"
    assert response.amount == pytest.approx(150.0)
    assert response.currency == Currency.RUB
    assert "payment/success" in response.payment_url


@pytest.mark.asyncio
async def test_create_payment_unsupported_provider_raises(settings_stub):
    service = PaymentService(settings_stub)

    request = PaymentRequest(
        subscription_tier="basic",
        amount=50.0,
        currency=Currency.USD,
        payment_method=PaymentMethod.BANK_CARD,
        provider=PaymentProvider.STRIPE,
        description="Test payment",
        user_id="1",
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_payment(request)

    assert exc.value.status_code == 400
    assert "Unsupported payment provider" in exc.value.detail


@pytest.mark.asyncio
async def test_check_payment_status_unsupported_provider(settings_stub):
    service = PaymentService(settings_stub)

    with pytest.raises(HTTPException) as exc:
        await service.check_payment_status("pid", PaymentProvider.STRIPE)

    assert exc.value.status_code == 400


def test_validate_payment_method_invalid_method(settings_stub):
    service = PaymentService(settings_stub)

    # For RUB region (RU) PayPal is not in available_methods
    request = PaymentRequest(
        subscription_tier="basic",
        amount=100.0,
        currency=Currency.RUB,
        payment_method=PaymentMethod.PAYPAL,
        provider=PaymentProvider.SBP,
        description="Test payment",
        user_id="1",
    )

    with pytest.raises(HTTPException) as exc:
        service._validate_payment_method(request)

    assert "not available" in exc.value.detail


@pytest.mark.asyncio
async def test_handle_sbp_webhook_happy_path(settings_stub, db_session):
    service = PaymentService(settings_stub)

    db_payment = DBPayment(
        user_id=1,
        amount=100.0,
        currency="RUB",
        status=DBPaymentStatus.PENDING,
        provider="sbp",
        provider_payment_id="sbp123",
        subscription_tier=DBSubscriptionTier.BASIC,
        description="Test",
    )
    db_session.add(db_payment)
    db_session.commit()

    data = {
        "payment_id": "sbp123",
        "amount": {"value": "100.0", "currency": "RUB"},
        "status": "paid",
    }

    await service._handle_sbp_webhook(data, db_session)

    db_session.refresh(db_payment)
    assert db_payment.status == DBPaymentStatus.COMPLETED
    assert db_payment.completed_at is not None

    subscription = (
        db_session.query(DBSubscription)
        .filter(DBSubscription.user_id == db_payment.user_id)
        .first()
    )
    assert subscription is not None
    assert subscription.tier == DBSubscriptionTier.BASIC


@pytest.mark.asyncio
async def test_handle_sbp_webhook_ignores_non_final_status(settings_stub, db_session):
    service = PaymentService(settings_stub)

    db_payment = DBPayment(
        user_id=1,
        amount=100.0,
        currency="RUB",
        status=DBPaymentStatus.PENDING,
        provider="sbp",
        provider_payment_id="sbp999",
        subscription_tier=DBSubscriptionTier.BASIC,
        description="Test",
    )
    db_session.add(db_payment)
    db_session.commit()

    data = {
        "payment_id": "sbp999",
        "amount": {"value": "100.0", "currency": "RUB"},
        "status": "processing",
    }

    await service._handle_sbp_webhook(data, db_session)

    db_session.refresh(db_payment)
    assert db_payment.status == DBPaymentStatus.PENDING


@pytest.mark.asyncio
async def test_handle_yookassa_webhook_happy_path(settings_stub, db_session):
    service = PaymentService(settings_stub)

    db_payment = DBPayment(
        user_id=2,
        amount=50.0,
        currency="RUB",
        status=DBPaymentStatus.PENDING,
        provider="yookassa",
        provider_payment_id="yk1",
        subscription_tier=None,
        description="Test",
    )
    db_session.add(db_payment)
    db_session.commit()

    data = {
        "object": {
            "id": "yk1",
            "status": "succeeded",
            "amount": {"value": "50.0", "currency": "RUB"},
            "metadata": {"subscription_tier": "pro"},
        }
    }

    await service._handle_yookassa_webhook(data, db_session)

    db_session.refresh(db_payment)
    assert db_payment.status == DBPaymentStatus.COMPLETED

    subscription = (
        db_session.query(DBSubscription)
        .filter(DBSubscription.user_id == db_payment.user_id)
        .first()
    )
    assert subscription is not None
    assert subscription.tier == DBSubscriptionTier.PRO
