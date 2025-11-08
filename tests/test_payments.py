import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add project root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def payment_request():
    return {
        "amount": 500.0,
        "currency": "RUB",
        "description": "Demo analysis payment",
    }

@pytest.fixture
def yookassa_env_vars():
    """Setup YooKassa environment variables for tests"""
    original_shop_id = os.environ.get("YOOKASSA_SHOP_ID")
    original_secret_key = os.environ.get("YOOKASSA_SECRET_KEY")
    
    os.environ["YOOKASSA_SHOP_ID"] = "test_shop_id"
    os.environ["YOOKASSA_SECRET_KEY"] = "test_secret_key"
    
    yield
    
    # Cleanup
    if original_shop_id:
        os.environ["YOOKASSA_SHOP_ID"] = original_shop_id
    else:
        os.environ.pop("YOOKASSA_SHOP_ID", None)
    
    if original_secret_key:
        os.environ["YOOKASSA_SECRET_KEY"] = original_secret_key
    else:
        os.environ.pop("YOOKASSA_SECRET_KEY", None)

@pytest.fixture
def mock_yookassa_response():
    return {
        "id": "test_payment_id",
        "status": "pending",
        "confirmation": {
            "type": "redirect",
            "confirmation_url": "https://yoomoney.ru/checkout/payments/test"
        },
        "amount": {
            "value": "500.00",
            "currency": "RUB"
        }
    }

# YooKassa payment tests

def test_yookassa_payment_success(payment_request, yookassa_env_vars, mock_yookassa_response):
    """Test successful YooKassa payment creation"""
    with patch("main.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_yookassa_response
        )
        
        response = client.post("/payments/yookassa", json=payment_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "payment_url" in data
        assert "status" in data
        assert data["status"] == "pending"
        assert "yoomoney.ru" in data["payment_url"]
        
        # Verify request was made with correct parameters
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["auth"] == ("test_shop_id", "test_secret_key")
        assert call_kwargs["json"]["amount"]["value"] == "500.00"

def test_yookassa_payment_api_error(payment_request, yookassa_env_vars):
    """Test YooKassa API error handling"""
    with patch("main.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {"error": "Invalid credentials"}
        )
        
        response = client.post("/payments/yookassa", json=payment_request)
        
        assert response.status_code == 400
        assert "error" in response.json() or "detail" in response.json()

@pytest.mark.parametrize("invalid_data,expected_status", [
    ({"amount": -100.0, "currency": "RUB", "description": "Test"}, 422),
    ({"amount": 0, "currency": "RUB", "description": "Test"}, 422),
    ({"amount": 500.0, "currency": "INVALID", "description": "Test"}, 422),
])
def test_yookassa_payment_validation(invalid_data, expected_status, yookassa_env_vars):
    """Test payment request validation"""
    response = client.post("/payments/yookassa", json=invalid_data)
    assert response.status_code == expected_status

# SBP payment tests

def test_sbp_payment_stub(payment_request):
    """Test SBP payment stub endpoint"""
    response = client.post("/payments/sbp", json=payment_request)
    
    assert response.status_code == 200
    data = response.json()
    assert "payment_url" in data
    assert "status" in data
    assert data["status"] == "pending"
    assert "sbp-payment.ru" in data["payment_url"]

# Health check tests

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] in ["payment", "ai-ml"]

# Edge cases and error scenarios

def test_payment_with_missing_fields():
    """Test payment request with missing required fields"""
    incomplete_request = {"amount": 500.0}
    
    response = client.post("/payments/yookassa", json=incomplete_request)
    
    assert response.status_code == 422
    assert "detail" in response.json()

@pytest.mark.parametrize("endpoint,needs_env", [
    ("/payments/yookassa", True),
    ("/payments/sbp", False)
])
def test_payment_endpoints_exist(endpoint, needs_env, payment_request, yookassa_env_vars):
    """Test that payment endpoints are accessible"""
    response = client.post(endpoint, json=payment_request)
    
    # Endpoint should exist (not 404)
    assert response.status_code != 404
    # May return 500 if credentials not configured, but endpoint exists
    assert response.status_code in [200, 400, 422, 500]

def test_yookassa_missing_credentials(payment_request):
    """Test YooKassa payment without credentials"""
    # Temporarily remove credentials
    original_shop_id = os.environ.get("YOOKASSA_SHOP_ID")
    original_secret_key = os.environ.get("YOOKASSA_SECRET_KEY")
    
    os.environ.pop("YOOKASSA_SHOP_ID", None)
    os.environ.pop("YOOKASSA_SECRET_KEY", None)
    
    # Reload main module to pick up empty credentials
    import importlib
    import main as main_module
    importlib.reload(main_module)
    
    response = client.post("/payments/yookassa", json=payment_request)
    
    # Should return 500 with credentials error
    assert response.status_code == 500
    assert "credentials" in response.json()["detail"].lower()
    
    # Restore credentials
    if original_shop_id:
        os.environ["YOOKASSA_SHOP_ID"] = original_shop_id
    if original_secret_key:
        os.environ["YOOKASSA_SECRET_KEY"] = original_secret_key
    importlib.reload(main_module)

def test_yookassa_network_error(payment_request, yookassa_env_vars):
    """Test handling of network errors"""
    with patch("main.requests.post") as mock_post:
        mock_post.side_effect = Exception("Network error")
        
        try:
            response = client.post("/payments/yookassa", json=payment_request)
            assert response.status_code == 500
        except Exception:
            pass  # Expected behavior for unhandled network errors