"""Unit tests for authentication service"""
import pytest
from unittest.mock import patch


class TestPasswordHashing:
    """Test password hashing"""

    def test_hash_password(self):
        """Test password hashing"""
        from src.server.features.auth.utils import hash_password
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_password(self):
        """Test password verification"""
        from src.server.features.auth.utils import hash_password, verify_password
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


class TestJWTTokens:
    """Test JWT token generation"""

    def test_create_access_token(self):
        """Test token creation"""
        from src.server.features.auth.utils import create_access_token
        user_id = "test_user_123"
        token = create_access_token(user_id)
        assert token is not None
        assert isinstance(token, str)
