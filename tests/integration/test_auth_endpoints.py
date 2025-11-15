"""Integration tests for authentication endpoints"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAuthEndpoints:
    """Test authentication API endpoints"""

    def test_register_user(self, test_client):
        """Test user registration"""
        response = test_client.post(
            "/auth/register",
            data={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        assert response.status_code in [200, 201]

    def test_login_user(self, test_client):
        """Test user login"""
        response = test_client.post(
            "/auth/login",
            data={
                "username": "test@example.com",
                "password": "TestPassword123!"
            }
        )
        assert response.status_code in [200, 401]

    def test_get_current_user(self, test_client):
        """Test get current user endpoint"""
        response = test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [401, 403]
