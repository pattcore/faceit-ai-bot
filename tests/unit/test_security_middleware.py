from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from src.server.middleware.security_middleware import SecurityMiddleware


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityMiddleware)

    @app.get("/test")
    def test_endpoint() -> dict:
        return {"ok": True}

    @app.get("/override")
    def override_endpoint() -> Response:
        # Endpoint sets its own headers; middleware should not override CSP/Permissions
        # but must still remove the Server header and add other security headers.
        return Response(
            content="{}",
            media_type="application/json",
            headers={
                "Content-Security-Policy": "custom-csp",
                "Permissions-Policy": "custom-permissions",
                "server": "uvicorn",
            },
        )

    return app


def test_security_middleware_sets_basic_headers() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/test")

    assert response.status_code == 200
    # Basic security headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert (
        response.headers["Strict-Transport-Security"]
        == "max-age=31536000; includeSubDomains"
    )
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    assert "Permissions-Policy" in response.headers
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    # Server header should be stripped if present
    assert "server" not in {k.lower(): v for k, v in response.headers.items()}


def test_security_middleware_preserves_existing_csp_and_permissions_and_removes_server() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/override")

    assert response.status_code == 200
    # Existing headers must be preserved, not overwritten
    assert response.headers["Content-Security-Policy"] == "custom-csp"
    assert response.headers["Permissions-Policy"] == "custom-permissions"
    # Middleware must remove the Server header
    assert "server" not in {k.lower(): v for k, v in response.headers.items()}
