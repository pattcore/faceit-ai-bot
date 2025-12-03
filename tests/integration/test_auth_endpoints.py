"""Integration tests for authentication endpoints"""
import pytest

from src.server.database.models import User
from src.server.auth.security import get_password_hash
from src.server.services.captcha_service import captcha_service, CaptchaProviderError


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

    def test_register_fails_when_captcha_invalid_and_user_not_created(
        self,
        test_client,
        db_session,
        monkeypatch,
    ):
        """Registration must fail when CAPTCHA is invalid and not create user."""

        email = "captcha-fail@example.com"

        # Force CAPTCHA to be enabled and return False for registration
        monkeypatch.setattr(captcha_service, "is_enabled", lambda: True)
        monkeypatch.setattr(captcha_service, "provider", "turnstile")

        async def fake_verify_turnstile(token, remote_ip=None, action=None):  # noqa: ARG001
            return False

        monkeypatch.setattr(captcha_service, "_verify_turnstile", fake_verify_turnstile)

        response = test_client.post(
            "/auth/register",
            data={
                "email": email,
                "username": "user1",
                "password": "TestPassword123!",
                "captcha_token": "dummy-token",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "CAPTCHA verification failed"

        # Ensure no user was created when CAPTCHA failed
        user = db_session.query(User).filter(User.email == email).first()
        assert user is None

    def test_login_allows_when_captcha_provider_error_fail_open(
        self,
        test_client,
        db_session,
        monkeypatch,
    ):
        """Login should succeed when CAPTCHA provider errors but fail-open is used."""

        email = "login-captcha@example.com"
        password = "password123"

        user = User(
            email=email,
            username="loginuser",
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Enable CAPTCHA and simulate provider infrastructure error for Turnstile
        monkeypatch.setattr(captcha_service, "is_enabled", lambda: True)
        monkeypatch.setattr(captcha_service, "provider", "turnstile")

        async def failing_turnstile(token, remote_ip=None, action=None):  # noqa: ARG001
            raise CaptchaProviderError("temporary provider error")

        monkeypatch.setattr(captcha_service, "_verify_turnstile", failing_turnstile)

        response = test_client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
                "captcha_token": "dummy-token",
            },
            headers={"Origin": "https://frontend.test"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
