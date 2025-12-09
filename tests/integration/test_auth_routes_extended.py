"""Extended integration tests for auth.routes.

Covers additional branches in register/login, Faceit callback guards,
Steam login, and Steam link/unlink endpoints.
"""

from datetime import datetime

import pytest

from src.server.auth import routes as auth_routes
from src.server.auth.security import get_password_hash
from src.server.config.settings import settings
from src.server.database.models import User, UserSession
from src.server.services.captcha_service import captcha_service
import src.server.integrations.faceit_client as faceit_client_module


@pytest.mark.integration
class TestAuthRoutesExtended:
    def test_register_invalid_email_format(self, test_client, monkeypatch):
        """Registration should fail with invalid email format."""

        # Bypass CAPTCHA so we test only email validation
        monkeypatch.setattr(captcha_service, "is_enabled", lambda: False)

        response = test_client.post(
            "/auth/register",
            data={
                "email": "invalid-email",
                "username": "user1",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid email format"

    def test_register_password_too_short(self, test_client, monkeypatch):
        """Registration should fail when password is too short."""

        monkeypatch.setattr(captcha_service, "is_enabled", lambda: False)

        response = test_client.post(
            "/auth/register",
            data={
                "email": "shortpass@example.com",
                "username": "user2",
                "password": "123",
            },
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Password must be at least 8 characters long and contain at least one letter and one digit"
        )

    def test_register_password_missing_complexity_returns_400(self, test_client, monkeypatch):
        """Registration should fail when password lacks required letter/digit complexity."""

        monkeypatch.setattr(captcha_service, "is_enabled", lambda: False)

        # 8 characters but only digits
        response = test_client.post(
            "/auth/register",
            data={
                "email": "weakpass@example.com",
                "username": "user3",
                "password": "12345678",
            },
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Password must be at least 8 characters long and contain at least one letter and one digit"
        )

    def test_register_duplicate_email_returns_400(self, test_client, db_session, monkeypatch):
        """Registration should fail when email is already registered."""

        monkeypatch.setattr(captcha_service, "is_enabled", lambda: False)

        email = "dupe@example.com"
        user = User(
            email=email,
            username="existing",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()

        response = test_client.post(
            "/auth/register",
            data={
                "email": email,
                "username": "newuser",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_login_inactive_user_returns_400(self, test_client, db_session, monkeypatch):
        """Inactive user should not be able to log in."""

        monkeypatch.setattr(captcha_service, "is_enabled", lambda: False)

        email = "inactive@example.com"
        password = "password123"
        user = User(
            email=email,
            username="inactive",
            hashed_password=get_password_hash(password),
            is_active=False,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()

        response = test_client.post(
            "/auth/login",
            data={"username": email, "password": password},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "User account is inactive"

    def test_login_invalid_credentials_returns_401(self, test_client, db_session, monkeypatch):
        """Login with wrong password should return 401."""

        monkeypatch.setattr(captcha_service, "is_enabled", lambda: False)

        email = "login@example.com"
        user = User(
            email=email,
            username="loginuser",
            hashed_password=get_password_hash("correct-password"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()

        response = test_client.post(
            "/auth/login",
            data={"username": email, "password": "wrong-password"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

    def test_faceit_callback_missing_code_or_state_returns_400(self, test_client):
        """Faceit callback should require both code and state."""

        response = test_client.get("/auth/faceit/callback")

        assert response.status_code == 400
        assert response.json()["detail"] == "Missing authorization code or state"

    def test_faceit_callback_invalid_state_returns_400(self, test_client, monkeypatch):
        """Faceit callback should reject invalid state token."""

        def fake_decode(token: str):  # noqa: ARG001
            return None

        monkeypatch.setattr(auth_routes, "decode_access_token", fake_decode)

        response = test_client.get("/auth/faceit/callback?code=abc&state=invalid")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid state parameter"

    def test_faceit_callback_state_missing_code_verifier_returns_400(self, test_client, monkeypatch):
        """Faceit callback should reject state without code_verifier (cv)."""

        def fake_decode(token: str):  # noqa: ARG001
            return {"sub": "faceit_oauth"}

        monkeypatch.setattr(auth_routes, "decode_access_token", fake_decode)

        response = test_client.get("/auth/faceit/callback?code=abc&state=valid")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid state parameter"

    def test_faceit_callback_creates_user_and_sets_cookie_and_redirect(self, test_client, db_session, monkeypatch):
        def fake_decode(token: str):  # noqa: ARG001
            return {"sub": "faceit_oauth", "cv": "test_verifier"}

        monkeypatch.setattr(auth_routes, "decode_access_token", fake_decode)

        monkeypatch.setattr(auth_routes.settings, "FACEIT_CLIENT_ID", "test-client-id", raising=False)
        monkeypatch.setattr(auth_routes.settings, "FACEIT_CLIENT_SECRET", "test-client-secret", raising=False)
        monkeypatch.setattr(auth_routes.settings, "WEBSITE_URL", "https://example.com", raising=False)

        userinfo = {
            "guid": "faceit-guid-123",
            "email": "faceit@example.com",
            "nickname": "FaceitNick",
        }

        class _FakeResponse:
            def __init__(self, status, json_data, text_data="") -> None:  # noqa: ANN001
                self.status = status
                self._json_data = json_data
                self._text_data = text_data

            async def __aenter__(self):  # noqa: D401
                return self

            async def __aexit__(self, exc_type, exc, tb):  # noqa: D401, ANN001
                return False

            async def json(self):  # noqa: D401
                return self._json_data

            async def text(self):  # noqa: D401
                return self._text_data

        class _FakeSession:
            def __init__(self, *args, **kwargs) -> None:  # noqa: ANN001
                self._post_response = _FakeResponse(200, {"access_token": "faceit-access-token"}, "ok")
                self._get_response = _FakeResponse(200, userinfo, "ok")

            async def __aenter__(self):  # noqa: D401
                return self

            async def __aexit__(self, exc_type, exc, tb):  # noqa: D401, ANN001
                return False

            def post(self, *args, **kwargs):  # noqa: ANN001
                return self._post_response

            def get(self, *args, **kwargs):  # noqa: ANN001
                return self._get_response

        class _FakeBasicAuth:  # noqa: D401
            def __init__(self, *args, **kwargs) -> None:  # noqa: ANN001
                self.args = args
                self.kwargs = kwargs

        monkeypatch.setattr(auth_routes.aiohttp, "ClientSession", lambda *args, **kwargs: _FakeSession(*args, **kwargs))
        monkeypatch.setattr(auth_routes.aiohttp, "BasicAuth", _FakeBasicAuth)

        class DummyFaceitClient:  # noqa: D401
            async def get_player_by_nickname(self, nickname):  # noqa: ANN001, ARG002
                return {"games": {"cs2": {"faceit_elo": 2000, "skill_level": 7}}}

        monkeypatch.setattr(faceit_client_module, "FaceitAPIClient", DummyFaceitClient)

        response = test_client.get(
            "/auth/faceit/callback?code=abc&state=dummy-state",
            follow_redirects=False,
        )

        assert response.status_code in (302, 303, 307)
        location = response.headers.get("location") or response.headers.get("Location")
        assert location is not None
        assert "/auth?faceit_token=" in location
        assert "&auto=1" in location

        user = (
            db_session.query(User)
            .filter(User.faceit_id == "faceit-guid-123")
            .first()
        )
        assert user is not None
        assert user.email == "faceit@example.com"
        assert user.last_login is not None
        assert user.login_count == 1

        set_cookie = response.headers.get("set-cookie") or ""
        assert "access_token=" in set_cookie

    def test_login_failed_attempts_trigger_redis_ban_and_lockout(self, test_client, db_session, monkeypatch):
        email = "throttle-login@example.com"
        correct_password = "password123"
        wrong_password = "wrong-password"

        user = User(
            email=email,
            username="login_throttle_user",
            hashed_password=get_password_hash(correct_password),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()

        class _DummyRedis:
            def __init__(self) -> None:
                self.counters: dict[str, int] = {}
                self.expires: dict[str, int] = {}
                self.storage: dict[str, str] = {}

            async def incr(self, key: str) -> int:
                self.counters[key] = self.counters.get(key, 0) + 1
                return self.counters[key]

            async def expire(self, key: str, ttl: int) -> None:
                self.expires[key] = ttl

            async def exists(self, key: str) -> int:
                return 1 if key in self.storage else 0

            async def ttl(self, key: str) -> int:
                return self.expires.get(key, -1)

            async def setex(self, key: str, ttl: int, value: str) -> None:
                self.storage[key] = value
                self.expires[key] = ttl

        dummy = _DummyRedis()

        monkeypatch.setattr(auth_routes.rate_limiter, "redis_client", dummy)
        monkeypatch.setattr(auth_routes.rate_limiter, "requests_per_minute", 1000, raising=False)
        monkeypatch.setattr(auth_routes.rate_limiter, "requests_per_hour", 1000, raising=False)

        monkeypatch.setattr(settings, "RATE_LIMIT_BAN_ENABLED", True, raising=False)
        monkeypatch.setattr(settings, "RATE_LIMIT_BAN_THRESHOLD", 2, raising=False)
        monkeypatch.setattr(settings, "RATE_LIMIT_BAN_WINDOW_SECONDS", 600, raising=False)
        monkeypatch.setattr(settings, "RATE_LIMIT_BAN_TTL_SECONDS", 3600, raising=False)

        headers = {"Origin": "chrome-extension://extension-id"}

        for _ in range(2):
            resp = test_client.post(
                "/auth/login",
                data={
                    "username": email,
                    "password": wrong_password,
                    "captcha_token": "dummy-token",
                },
                headers=headers,
            )
            assert resp.status_code == 401

        viol_keys = [k for k in dummy.counters.keys() if k.startswith("rate:viol:ip:")]
        assert viol_keys

        ban_keys = [k for k in dummy.storage.keys() if k.startswith("rate:ban:ip:")]
        assert ban_keys

        resp3 = test_client.post(
            "/auth/login",
            data={
                "username": email,
                "password": wrong_password,
                "captcha_token": "dummy-token",
            },
            headers=headers,
        )
        assert resp3.status_code == 429
        assert "temporarily blocked" in resp3.json()["detail"]

    def test_steam_login_redirects_when_captcha_ok(self, test_client, monkeypatch):
        """Steam login should redirect to Steam OpenID when CAPTCHA passes."""

        async def ok_verify(token, remote_ip=None, action=None, fail_open_on_error=False):  # noqa: ARG001, ARG002
            return True

        monkeypatch.setattr(captcha_service, "verify_token", ok_verify)

        response = test_client.get(
            "/auth/steam/login?captcha_token=dummy",
            follow_redirects=False,
        )

        assert response.status_code in (302, 303, 307)
        location = response.headers.get("location") or response.headers.get("Location")
        assert location is not None
        assert "steamcommunity.com/openid/login" in location

    def test_steam_login_captcha_invalid_still_redirects_fail_open(self, test_client, monkeypatch):
        """Steam login should still redirect when CAPTCHA verification fails (fail-open)."""

        async def bad_verify(token, remote_ip=None, action=None, fail_open_on_error=False):  # noqa: ARG001, ARG002
            return False

        monkeypatch.setattr(captcha_service, "verify_token", bad_verify)

        response = test_client.get(
            "/auth/steam/login?captcha_token=dummy",
            follow_redirects=False,
        )

        assert response.status_code in (302, 303, 307)
        location = response.headers.get("location") or response.headers.get("Location")
        assert location is not None
        assert "steamcommunity.com/openid/login" in location

    def test_link_steam_account_success(self, authenticated_client, db_session):
        """Authenticated user can link a new Steam account."""

        # There should be exactly one user created by authenticated_client fixture
        current_user = db_session.query(User).first()
        assert current_user is not None
        assert current_user.steam_id is None

        response = authenticated_client.post(
            "/auth/steam/link",
            json={"steam_id": "76561198000000000"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["steam_id"] == "76561198000000000"

        db_session.refresh(current_user)
        assert current_user.steam_id == "76561198000000000"

    def test_link_steam_account_conflict_returns_400(self, authenticated_client, db_session):
        """Linking Steam ID already used by another user should fail."""

        # Create another user that already uses this steam_id
        conflict_user = User(
            email="conflict@example.com",
            username="conflict",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            created_at=datetime.utcnow(),
            steam_id="76561198000000001",
        )
        db_session.add(conflict_user)
        db_session.commit()

        response = authenticated_client.post(
            "/auth/steam/link",
            json={"steam_id": "76561198000000001"},
        )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "This Steam account is already linked to another user"
        )

    def test_unlink_steam_account_clears_steam_id(self, authenticated_client, db_session):
        """Unlink endpoint should remove steam_id from current user."""

        current_user = db_session.query(User).first()
        assert current_user is not None

        current_user.steam_id = "76561198000000002"
        db_session.add(current_user)
        db_session.commit()

        response = authenticated_client.post("/auth/steam/unlink")

        assert response.status_code == 200
        data = response.json()
        assert data["steam_id"] is None

        db_session.refresh(current_user)
        assert current_user.steam_id is None

    def test_login_updates_last_login_login_count_and_active_users_metric(
        self,
        test_client,
        db_session,
        monkeypatch,
    ):
        """Successful login should update last_login, increment login_count and ACTIVE_USERS."""

        class DummyCounter:
            def __init__(self) -> None:
                self.calls = 0

            def inc(self) -> None:
                self.calls += 1

        dummy_counter = DummyCounter()
        monkeypatch.setattr(auth_routes, "ACTIVE_USERS", dummy_counter)

        email = "metric-login@example.com"
        password = "password123"

        user = User(
            email=email,
            username="metric_user",
            hashed_password=get_password_hash(password),
            is_active=True,
            created_at=datetime.utcnow(),
            login_count=5,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.last_login is None
        assert user.login_count == 5

        response = test_client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
                "captcha_token": "dummy-token",
            },
            # Chrome extension origin skips CAPTCHA verification path
            headers={"Origin": "chrome-extension://extension-id"},
        )

        assert response.status_code == 200

        db_session.refresh(user)
        assert user.login_count == 6
        assert isinstance(user.last_login, datetime)

        assert dummy_counter.calls == 1


    def test_login_sets_refresh_cookie_and_creates_session(self, test_client, db_session):
        """Successful login should set refresh_token cookie and create UserSession row."""

        email = "refresh-login@example.com"
        password = "password123"

        user = User(
            email=email,
            username="refresh_user",
            hashed_password=get_password_hash(password),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        response = test_client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
                "captcha_token": "dummy-token",
            },
            # Chrome extension origin skips CAPTCHA verification path
            headers={"Origin": "chrome-extension://extension-id"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # Both access and refresh cookies should be set
        set_cookie = response.headers.get("set-cookie") or ""
        assert "access_token=" in set_cookie
        assert "refresh_token=" in set_cookie

        sessions = (
            db_session.query(UserSession)
            .filter(UserSession.user_id == user.id)
            .all()
        )
        assert len(sessions) == 1
        assert sessions[0].revoked_at is None


    def test_refresh_rotates_tokens_and_sessions(self, test_client, db_session):
        """POST /auth/refresh should issue new access/refresh tokens and rotate sessions."""

        email = "refresh-flow@example.com"
        password = "password123"

        user = User(
            email=email,
            username="refresh_flow_user",
            hashed_password=get_password_hash(password),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        login_resp = test_client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
                "captcha_token": "dummy-token",
            },
            headers={"Origin": "chrome-extension://extension-id"},
        )

        assert login_resp.status_code == 200
        first_access = login_resp.json()["access_token"]
        first_refresh = test_client.cookies.get("refresh_token")
        assert first_refresh

        refresh_resp = test_client.post("/auth/refresh")

        assert refresh_resp.status_code == 200
        second_access = refresh_resp.json()["access_token"]
        assert second_access
        # Access token should change when refreshed
        assert second_access != first_access

        second_refresh = test_client.cookies.get("refresh_token")
        assert second_refresh
        assert second_refresh != first_refresh

        sessions = (
            db_session.query(UserSession)
            .filter(UserSession.user_id == user.id)
            .all()
        )
        assert len(sessions) == 2
        revoked = [s for s in sessions if s.revoked_at is not None]
        active = [s for s in sessions if s.revoked_at is None]
        assert len(revoked) == 1
        assert len(active) == 1


    def test_refresh_with_invalid_cookie_returns_401_and_clears_cookie(
        self,
        test_client,
        db_session,
    ):
        """Refreshing with invalid refresh_token cookie should return 401 and clear cookie."""

        email = "refresh-invalid@example.com"
        password = "password123"

        user = User(
            email=email,
            username="refresh_invalid_user",
            hashed_password=get_password_hash(password),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        login_resp = test_client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
                "captcha_token": "dummy-token",
            },
            headers={"Origin": "chrome-extension://extension-id"},
        )

        assert login_resp.status_code == 200
        assert test_client.cookies.get("refresh_token")

        # Overwrite refresh_token cookie with an invalid value
        test_client.cookies.set("refresh_token", "invalid-refresh-token")

        resp = test_client.post("/auth/refresh")

        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or expired refresh token"

        # Cookie should be cleared via Set-Cookie header
        set_cookie = resp.headers.get("set-cookie") or ""
        assert "refresh_token=" in set_cookie


    def test_logout_revokes_refresh_session_and_clears_cookies(
        self,
        test_client,
        db_session,
    ):
        """Logout should revoke current refresh session and clear auth cookies."""

        email = "logout-refresh@example.com"
        password = "password123"

        user = User(
            email=email,
            username="logout_refresh_user",
            hashed_password=get_password_hash(password),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        login_resp = test_client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
                "captcha_token": "dummy-token",
            },
            headers={"Origin": "chrome-extension://extension-id"},
        )

        assert login_resp.status_code == 200
        assert test_client.cookies.get("access_token")
        assert test_client.cookies.get("refresh_token")

        sessions_before = (
            db_session.query(UserSession)
            .filter(UserSession.user_id == user.id)
            .all()
        )
        assert len(sessions_before) == 1
        assert sessions_before[0].revoked_at is None

        logout_resp = test_client.post("/auth/logout")

        assert logout_resp.status_code == 200
        assert logout_resp.json()["detail"] == "Logged out"

        sessions_after = (
            db_session.query(UserSession)
            .filter(UserSession.user_id == user.id)
            .all()
        )
        assert len(sessions_after) == 1
        assert sessions_after[0].revoked_at is not None

        # TestClient cookie jar should no longer have auth cookies
        assert test_client.cookies.get("access_token") is None
        assert test_client.cookies.get("refresh_token") is None

    def test_steam_callback_creates_user_and_sets_cookie_and_redirect(self, test_client, db_session, monkeypatch):
        """Steam callback should create a new user, update login activity and redirect with token."""

        async def fake_verify_steam_openid(query_params):  # noqa: ARG001
            return "76561198000009999"

        async def fake_fetch_persona(steam_id: str):  # noqa: ARG001
            return "TestPersona"

        monkeypatch.setattr(auth_routes, "verify_steam_openid", fake_verify_steam_openid)
        monkeypatch.setattr(auth_routes, "fetch_steam_persona_name", fake_fetch_persona)

        response = test_client.get(
            "/auth/steam/callback?dummy=1",
            follow_redirects=False,
        )

        assert response.status_code in (302, 303, 307)
        location = response.headers.get("location") or response.headers.get("Location")
        assert location is not None
        assert "/auth?steam_token=" in location

        # New user should be created with given steam_id
        user = (
            db_session.query(User)
            .filter(User.steam_id == "76561198000009999")
            .first()
        )
        assert user is not None
        assert user.last_login is not None
        assert user.login_count == 1

        # access_token cookie should be set
        set_cookie = response.headers.get("set-cookie") or ""
        assert "access_token=" in set_cookie
