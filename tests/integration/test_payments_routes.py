"""Integration tests for /payments routes."""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from src.server.main import app as fastapi_app
from src.server.database.models import Payment, SubscriptionTier, User
from src.server.features.payments.models import (
    Currency,
    PaymentMethod,
    PaymentProvider,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
)
from src.server.features.payments.routes import get_payment_service
from src.server.services.captcha_service import captcha_service
from src.server.core.structured_logging import business_logger


pytestmark = pytest.mark.integration


class DummyPaymentService:
    def __init__(
        self,
        *,
        create_response: Optional[PaymentResponse] = None,
        status_response: Optional[PaymentStatus] = None,
    ):
        now = datetime.utcnow()
        self._create_response = create_response or PaymentResponse(
            payment_id="dummy-payment",
            status="pending",
            payment_url="https://example.com/pay",
            amount=49.99,
            currency=Currency.RUB,
            created_at=now,
            expires_at=now + timedelta(minutes=15),
            confirmation_type="redirect",
        )
        self._status_response = status_response or PaymentStatus(
            payment_id="dummy-payment",
            status="pending",
            paid=False,
            amount=49.99,
            currency=Currency.RUB,
            payment_method=PaymentMethod.SBP,
            created_at=now,
            paid_at=None,
        )
        self.create_requests: list[PaymentRequest] = []
        self.status_requests: list[tuple[str, PaymentProvider]] = []

    async def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        self.create_requests.append(request)
        return self._create_response

    async def check_payment_status(
        self, payment_id: str, provider: PaymentProvider
    ) -> PaymentStatus:
        self.status_requests.append((payment_id, provider))
        return self._status_response


def _override_payment_service(service):
    fastapi_app.dependency_overrides[get_payment_service] = lambda: service


def _clear_payment_service_override():
    fastapi_app.dependency_overrides.pop(get_payment_service, None)


def _get_current_user(db_session) -> User:
    return db_session.query(User).order_by(User.id.desc()).first()


@pytest.fixture(autouse=True)
def patch_business_logger(monkeypatch):
    monkeypatch.setattr(business_logger, "log_payment_event", lambda *_, **__: None)


def test_create_payment_success_persists_db_record(
    authenticated_client, db_session, monkeypatch
):
    service = DummyPaymentService()
    _override_payment_service(service)
    monkeypatch.setattr(
        captcha_service, "verify_token", lambda **_: True
    )

    try:
        payload = {
            "subscription_tier": "basic",
            "amount": 49.99,
            "currency": "RUB",
            "payment_method": "sbp",
            "provider": "sbp",
            "description": "Monthly",
            "captcha_token": "ok",
        }

        response = authenticated_client.post("/payments/create", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["payment_id"] == service._create_response.payment_id
        assert body["status"] == "pending"

        user = _get_current_user(db_session)
        db_payment = (
            db_session.query(Payment)
            .filter(Payment.provider_payment_id == service._create_response.payment_id)
            .first()
        )
        assert db_payment is not None
        assert db_payment.user_id == user.id
        assert db_payment.subscription_tier == SubscriptionTier.BASIC
    finally:
        _clear_payment_service_override()


def test_create_payment_invalid_captcha_returns_400(
    authenticated_client, db_session, monkeypatch
):
    service = DummyPaymentService()
    _override_payment_service(service)
    monkeypatch.setattr(
        captcha_service, "verify_token", lambda **_: False
    )

    try:
        payload = {
            "subscription_tier": "basic",
            "amount": 49.99,
            "currency": "RUB",
            "payment_method": "sbp",
            "provider": "sbp",
            "description": "Monthly",
            "captcha_token": "bad",
        }

        response = authenticated_client.post("/payments/create", json=payload)

        assert response.status_code == 400
        assert response.json()["detail"] == "CAPTCHA verification failed"
        assert service.create_requests == []
        assert (
            db_session.query(Payment)
            .filter(Payment.provider_payment_id == service._create_response.payment_id)
            .first()
            is None
        )
    finally:
        _clear_payment_service_override()


def test_create_payment_invalid_subscription_tier_returns_400(
    authenticated_client, db_session, monkeypatch
):
    service = DummyPaymentService()
    _override_payment_service(service)
    monkeypatch.setattr(
        captcha_service, "verify_token", lambda **_: True
    )

    try:
        payload = {
            "subscription_tier": "invalid",
            "amount": 49.99,
            "currency": "USD",
            "payment_method": "bank_card",
            "provider": "yookassa",
            "description": "Monthly",
            "captcha_token": "ok",
        }

        response = authenticated_client.post("/payments/create", json=payload)

        assert response.status_code == 400
        assert "Invalid subscription tier" in response.json()["detail"]
        assert len(service.create_requests) == 1
        assert (
            db_session.query(Payment)
            .filter(Payment.provider_payment_id == service._create_response.payment_id)
            .first()
            is None
        )
    finally:
        _clear_payment_service_override()


def test_check_payment_status_returns_service_payload(
    authenticated_client, db_session, monkeypatch
):
    user = _get_current_user(db_session)
    db_payment = Payment(
        user_id=user.id,
        amount=25.0,
        currency="RUB",
        provider="sbp",
        provider_payment_id="status-ok",
        subscription_tier=SubscriptionTier.BASIC,
    )
    db_session.add(db_payment)
    db_session.commit()

    status_response = PaymentStatus(
        payment_id="status-ok",
        status="completed",
        paid=True,
        amount=25.0,
        currency=Currency.RUB,
        payment_method=PaymentMethod.SBP,
        created_at=datetime.utcnow(),
        paid_at=datetime.utcnow(),
    )
    service = DummyPaymentService(status_response=status_response)
    _override_payment_service(service)

    try:
        response = authenticated_client.get(
            "/payments/status/status-ok",
            params={"provider": "sbp"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "completed"
        assert payload["paid"] is True
        assert service.status_requests == [("status-ok", PaymentProvider.SBP)]
    finally:
        _clear_payment_service_override()


def test_check_payment_status_returns_404_for_missing_payment(
    authenticated_client, db_session
):
    other_user = User(
        email="other@example.com",
        username="other",
        hashed_password="hash",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db_session.add(other_user)
    db_session.commit()

    db_payment = Payment(
        user_id=other_user.id,
        amount=10.0,
        currency="RUB",
        provider="sbp",
        provider_payment_id="status-missing",
        subscription_tier=SubscriptionTier.BASIC,
    )
    db_session.add(db_payment)
    db_session.commit()

    response = authenticated_client.get(
        "/payments/status/status-missing",
        params={"provider": "sbp"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"
