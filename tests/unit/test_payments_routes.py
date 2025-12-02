"""Unit tests for payments routes"""

from unittest.mock import Mock, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.server.features.payments.routes import (
    router,
    get_payment_service,
)
from src.server.features.payments.models import REGION_PAYMENT_CONFIG, PaymentProvider
from src.server.config.settings import settings


@pytest.fixture
def app():
    """FastAPI app with payments router only."""
    # Ensure test mode so webhooks skip strict auth/signature checks
    settings.TEST_ENV = True
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_payment_service():
    service = Mock()
    service.process_webhook = AsyncMock()
    return service


@pytest.fixture
def client(app, mock_payment_service):
    app.dependency_overrides[get_payment_service] = lambda: mock_payment_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_payment_methods_ru(client):
    """Should return RegionPaymentMethods config for RU region."""
    response = client.get("/payments/methods/RU")

    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "RU"
    assert len(data["available_methods"]) == len(
        REGION_PAYMENT_CONFIG["RU"].available_methods
    )


def test_get_payment_methods_unsupported_region(client):
    response = client.get("/payments/methods/UNKNOWN")

    assert response.status_code == 400


def test_sbp_webhook_success(client, mock_payment_service):
    payload = {"payment_id": "sbp123"}

    response = client.post("/payments/webhook/sbp", json=payload)

    assert response.status_code == 200
    mock_payment_service.process_webhook.assert_awaited_once()
    args, _ = mock_payment_service.process_webhook.call_args
    assert args[0] == PaymentProvider.SBP
    assert args[1]["payment_id"] == "sbp123"


def test_yookassa_webhook_success(client, mock_payment_service):
    payload = {"object": {"id": "yk1"}}

    response = client.post("/payments/webhook/yookassa", json=payload)

    assert response.status_code == 200
    mock_payment_service.process_webhook.assert_awaited()
    args, _ = mock_payment_service.process_webhook.call_args
    assert args[0] == PaymentProvider.YOOKASSA


def test_qiwi_webhook_success(client, mock_payment_service):
    payload = {"payment": {"id": "q1"}}

    response = client.post("/payments/webhook/qiwi", json=payload)

    assert response.status_code == 200
    mock_payment_service.process_webhook.assert_awaited()
    args, _ = mock_payment_service.process_webhook.call_args
    assert args[0] == PaymentProvider.QIWI
