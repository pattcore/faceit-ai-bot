"""Unit tests for auth.dependencies helpers.

Covers get_current_user, get_optional_current_user,
get_current_active_user, get_current_admin_user.
"""

from typing import Optional

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.server.auth.dependencies import (
    get_current_user,
    get_optional_current_user,
    get_current_active_user,
    get_current_admin_user,
)
from src.server.auth import dependencies as auth_deps
from src.server.database.connection import get_db
from src.server.database.models import Base, User


@pytest.fixture
def db_session():
    """In-memory SQLite session bound to app models Base."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_user(db_session, **overrides) -> User:
    user = User(
        email=overrides.get("email", "user@example.com"),
        username=overrides.get("username", "testuser"),
        hashed_password="hashed",
        is_active=overrides.get("is_active", True),
        is_admin=overrides.get("is_admin", False),
        created_at=overrides.get("created_at"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def app(db_session):
    """Minimal FastAPI app using auth dependencies with overridden DB."""
    app = FastAPI()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    @app.get("/me")
    async def read_me(user: User = Depends(get_current_user)):
        return {"id": user.id, "email": user.email}

    @app.get("/me-optional")
    async def read_me_optional(user: Optional[User] = Depends(get_optional_current_user)):
        return {"user_id": user.id if user else None}

    @app.get("/me-active")
    async def read_me_active(user: User = Depends(get_current_active_user)):
        return {"id": user.id}

    @app.get("/me-admin")
    async def read_me_admin(user: User = Depends(get_current_admin_user)):
        return {"id": user.id}

    return app


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token_uses_db_user(monkeypatch, client, db_session):
    user = create_user(db_session, email="valid@example.com")

    def fake_decode(token: str):  # noqa: ARG001
        return {"sub": user.id}

    monkeypatch.setattr(auth_deps, "decode_access_token", fake_decode)

    response = client.get("/me", headers={"Authorization": "Bearer testtoken"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == "valid@example.com"


@pytest.mark.asyncio
async def test_get_current_user_without_token_raises_401(client):
    response = client.get("/me")

    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_raises_401(monkeypatch, client):
    def fake_decode(token: str):  # noqa: ARG001
        return None

    monkeypatch.setattr(auth_deps, "decode_access_token", fake_decode)

    response = client.get("/me", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_missing_user_raises_401(monkeypatch, db_session):
    def fake_decode(token: str):  # noqa: ARG001
        return {"sub": 999999}

    monkeypatch.setattr(auth_deps, "decode_access_token", fake_decode)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/me",
        "headers": [],
        "client": ("testclient", 50000),
    }
    request = Request(scope)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request=request, token="testtoken", db=db_session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_optional_current_user_no_token_returns_none(client):
    response = client.get("/me-optional")

    assert response.status_code == 200
    assert response.json()["user_id"] is None


@pytest.mark.asyncio
async def test_get_optional_current_user_invalid_token_returns_none(monkeypatch, client):
    def fake_decode(token: str):  # noqa: ARG001
        raise ValueError("Invalid token")

    monkeypatch.setattr(auth_deps, "decode_access_token", fake_decode)

    response = client.get("/me-optional", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 200
    assert response.json()["user_id"] is None


@pytest.mark.asyncio
async def test_get_optional_current_user_valid_token_returns_user(monkeypatch, client, db_session):
    user = create_user(db_session, email="opt@example.com")

    def fake_decode(token: str):  # noqa: ARG001
        return {"sub": user.id}

    monkeypatch.setattr(auth_deps, "decode_access_token", fake_decode)

    response = client.get("/me-optional", headers={"Authorization": "Bearer sometoken"})

    assert response.status_code == 200
    assert response.json()["user_id"] == user.id


@pytest.mark.asyncio
async def test_get_current_active_user_inactive_raises(client, db_session, app):
    inactive_user = create_user(db_session, email="inactive@example.com", is_active=False)

    app.dependency_overrides[get_current_user] = lambda: inactive_user

    with TestClient(app) as local_client:
        response = local_client.get("/me-active")

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"


@pytest.mark.asyncio
async def test_get_current_active_user_ok(client, db_session, app):
    active_user = create_user(db_session, email="active@example.com", is_active=True)

    app.dependency_overrides[get_current_user] = lambda: active_user

    with TestClient(app) as local_client:
        response = local_client.get("/me-active")

    assert response.status_code == 200
    assert response.json()["id"] == active_user.id


@pytest.mark.asyncio
async def test_get_current_admin_user_not_admin_raises(client, db_session, app):
    non_admin = create_user(db_session, email="user@example.com", is_active=True, is_admin=False)

    app.dependency_overrides[get_current_active_user] = lambda: non_admin

    with TestClient(app) as local_client:
        response = local_client.get("/me-admin")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_get_current_admin_user_ok(client, db_session, app):
    admin_user = create_user(db_session, email="admin@example.com", is_active=True, is_admin=True)

    app.dependency_overrides[get_current_active_user] = lambda: admin_user

    with TestClient(app) as local_client:
        response = local_client.get("/me-admin")

    assert response.status_code == 200
    assert response.json()["id"] == admin_user.id


@pytest.mark.asyncio
async def test_get_current_user_payload_without_sub_raises_401(monkeypatch, db_session):
    """If JWT payload has no 'sub', dependency should return 401."""

    def fake_decode(token: str):  # noqa: ARG001
        return {}

    monkeypatch.setattr(auth_deps, "decode_access_token", fake_decode)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/me",
        "headers": [],
        "client": ("testclient", 50000),
    }
    request = Request(scope)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request=request, token="testtoken", db=db_session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_optional_current_user_payload_without_sub_returns_none(monkeypatch, client):
    """Optional current user should return None when payload has no 'sub'."""

    def fake_decode(token: str):  # noqa: ARG001
        return {}

    monkeypatch.setattr(auth_deps, "decode_access_token", fake_decode)

    response = client.get("/me-optional", headers={"Authorization": "Bearer token"})

    assert response.status_code == 200
    assert response.json()["user_id"] is None
