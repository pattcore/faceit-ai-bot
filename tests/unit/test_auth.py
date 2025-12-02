"""Tests for authentication

Legacy auth endpoint tests are skipped in favour of integration tests in
tests/integration/test_auth_endpoints.py, которые используют тестовые фикстуры
БД и настроенный TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from src.server.auth.security import get_password_hash
from src.server.main import app


pytestmark = pytest.mark.skip(
    reason="Replaced by integration tests in tests/integration/test_auth_endpoints.py",
)


client = TestClient(app)


def test_register_user():
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data


def test_login_user():
    """Test user login"""
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user():
    """Test get current user with token"""
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_password_hashing():
    """Test password hashing"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 0
