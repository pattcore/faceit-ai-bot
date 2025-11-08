import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt
from server.main import app
from server.core.config import settings

client = TestClient(app)

@pytest.fixture
def test_token():
    """Create a test JWT token"""
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "scope": "standard"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def test_api_health():
    """Test API health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_api_rate_limiting():
    """Test rate limiting middleware"""
    # Make multiple requests in quick succession
    responses = []
    for _ in range(10):
        responses.append(client.get("/api/health"))
    
    # Check if rate limiting is working
    assert any(r.status_code == 429 for r in responses), "Rate limiting not working"

def test_protected_endpoint_no_token():
    """Test protected endpoint without token"""
    response = client.get("/api/protected/user-info")
    assert response.status_code == 401
    assert "detail" in response.json()

def test_protected_endpoint_with_token(test_token):
    """Test protected endpoint with valid token"""
    response = client.get(
        "/api/protected/user-info",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["user_id"] == "test_user"

def test_invalid_token():
    """Test endpoint with invalid token"""
    response = client.get(
        "/api/protected/user-info",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()

def test_expired_token():
    """Test endpoint with expired token"""
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() - timedelta(minutes=30),
        "scope": "standard"
    }
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    response = client.get(
        "/api/protected/user-info",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "token expired" in response.json()["detail"].lower()

@pytest.mark.parametrize("endpoint", [
    "/api/demo/analyze",
    "/api/payments/create",
    "/api/user/profile",
    "/api/stats/summary"
])
def test_endpoint_error_handling(endpoint):
    """Test error handling for various endpoints"""
    # Test without required parameters
    response = client.post(endpoint, json={})
    assert response.status_code in [400, 401, 422]
    
    # Test with invalid data
    response = client.post(endpoint, json={"invalid": "data"})
    assert response.status_code in [400, 401, 422]
    
    # Test with invalid content type
    response = client.post(
        endpoint,
        data="invalid data",
        headers={"Content-Type": "text/plain"}
    )
    assert response.status_code in [400, 415]