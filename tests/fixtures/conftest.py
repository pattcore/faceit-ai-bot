import pytest
from fastapi.testclient import TestClient
from src.server.main import create_app
import os

@pytest.fixture(scope="session")
def test_app():
    # Set test environment variables
    os.environ["YOOKASSA_SHOP_ID"] = "test_shop_id"
    os.environ["YOOKASSA_SECRET_KEY"] = "test_secret_key"
    os.environ["TEST_ENV"] = "true"
    
    app = create_app()
    return app

@pytest.fixture(scope="session")
def client(test_app):
    return TestClient(test_app)

@pytest.fixture
def payment_request():
    return {
        "amount": 500.0,
        "currency": "RUB",
        "description": "Demo analysis payment"
    }

@pytest.fixture
def invalid_payment_request():
    return {
        "amount": -100.0,
        "currency": "INVALID",
        "description": ""
    }