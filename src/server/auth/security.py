"""JWT and password security"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
import secrets
import hashlib

from ..config.settings import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def _normalize_password(password: str) -> bytes:
    """Encode password to bytes and truncate to 72 bytes for bcrypt compatibility."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    password_bytes = _normalize_password(plain_password)
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt with proper length handling."""
    password_bytes = _normalize_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    now = datetime.utcnow()
    to_encode["jti"] = secrets.token_urlsafe(16)

    if expires_delta is not None:
        expire = now + expires_delta
    else:
        minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 30)
        expire = now + timedelta(minutes=minutes)

    exp_ts = int(expire.replace(tzinfo=timezone.utc).timestamp())
    to_encode["exp"] = exp_ts

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        return None


def create_refresh_token() -> str:
    """Generate a strong random refresh token string."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token with SHA-256 for safe storage in DB."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
