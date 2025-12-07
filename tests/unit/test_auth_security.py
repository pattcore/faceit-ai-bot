import pytest

from datetime import datetime, timedelta, timezone

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

    fixed_now = datetime(2030, 1, 1, 12, 0, 0)

    class _FixedDatetime(datetime):  # type: ignore[misc]
        @classmethod
        def utcnow(cls):  # type: ignore[override]
            return fixed_now

    # Patch datetime used inside security module so exp is deterministic
    monkeypatch.setattr(security, "datetime", _FixedDatetime)

    data = {"sub": "123"}
    token = security.create_access_token(data)

    payload = security.decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "123"

    exp_ts = payload["exp"]
    expected_exp_ts = int(
        (fixed_now + timedelta(minutes=5)).replace(tzinfo=timezone.utc).timestamp()
    )
    assert exp_ts == expected_exp_ts


def test_decode_expired_access_token_returns_none() -> None:
    data = {"sub": "123"}
    token = security.create_access_token(data, expires_delta=timedelta(seconds=-1))

    payload = security.decode_access_token(token)

    assert payload is None


def test_create_refresh_token_and_hash_roundtrip() -> None:
    token1 = security.create_refresh_token()
    token2 = security.create_refresh_token()

    assert isinstance(token1, str)
    assert isinstance(token2, str)
    assert token1 != token2

    hash1 = security.hash_refresh_token(token1)
    hash2 = security.hash_refresh_token(token1)
    hash3 = security.hash_refresh_token(token2)

    assert isinstance(hash1, str)
    assert hash1 == hash2
    assert hash1 != hash3
