"""Unit tests for authentication service"""


class TestPasswordHashing:
    """Test password hashing"""

    def test_hash_password(self):
        """Test password hashing"""
        from src.server.auth.security import get_password_hash

        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20

    def test_verify_password(self):
        """Test password verification"""
        from src.server.auth.security import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


class TestJWTTokens:
    """Test JWT token generation"""

    def test_create_access_token(self):
        """Test token creation"""
        from src.server.auth.security import create_access_token

        user_id = "test_user_123"
        token = create_access_token(data={"sub": user_id})
        assert token is not None
        assert isinstance(token, str)
