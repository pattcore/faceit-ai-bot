import pytest

from datetime import datetime, timedelta

from src.server.auth import security


def test_get_password_hash_and_verify_roundtrip() -> None:
    password = "test-password-123"

    hashed = security.get_password_hash(password)

    assert hashed != password
    assert security.verify_password(password, hashed) is True
    assert security.verify_password("wrong-password", hashed) is False


def test_verify_password_invalid_hash_returns_false() -> None:
    # Non-bcrypt string should not crash and must return False
    assert security.verify_password("password", "not-a-bcrypt-hash") is False


def test_long_password_is_truncated_for_bcrypt_but_still_verifies() -> None:
    # bcrypt uses only first 72 bytes; our helper truncates explicitly
    long_password = "a" * 100
    similar_password = "a" * 72 + "b" * 28

    hashed = security.get_password_hash(long_password)

    # Both passwords share first 72 bytes, so both should verify
    assert security.verify_password(long_password, hashed) is True
    assert security.verify_password(similar_password, hashed) is True


def test_create_and_decode_access_token_roundtrip() -> None:
    data = {"sub": "123", "scope": "test"}
    token = security.create_access_token(data, expires_delta=timedelta(minutes=5))

    payload = security.decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["scope"] == "test"
    assert "exp" in payload


def test_decode_access_token_invalid_returns_none() -> None:
    assert security.decode_access_token("this-is-not-a-jwt") is None


def test_create_access_token_uses_settings_default_expire(monkeypatch) -> None:
    # Ensure default expiration reads from settings.ACCESS_TOKEN_EXPIRE_MINUTES
    monkeypatch.setattr(security.settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 5, raising=False)

    data = {"sub": "123"}
    token = security.create_access_token(data)

    payload = security.decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "123"

    now_ts = datetime.utcnow().timestamp()
    exp_ts = payload["exp"]
    # Expect expiration to be approximately 5 minutes from now
    assert 5 * 60 - 15 <= exp_ts - now_ts <= 5 * 60 + 15
