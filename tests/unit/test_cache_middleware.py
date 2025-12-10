from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.server.middleware.cache_middleware as cache_mw
from src.server.middleware.cache_middleware import CacheMiddleware


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        # TTL is ignored in the dummy implementation
        self.store[key] = value

    def keys(self, pattern: str) -> list[str]:
        # Support patterns used by invalidate_cache / clear_all_cache
        if pattern == "api_cache:*":
            return [k for k in self.store.keys() if k.startswith("api_cache:")]
        if pattern.startswith("api_cache:*") and pattern.endswith("*"):
            inner = pattern[len("api_cache:*") : -1]
            return [
                k
                for k in self.store.keys()
                if k.startswith("api_cache:") and inner in k
            ]
        return []

    def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                deleted += 1
        return deleted


class DummyRedisError(DummyRedis):
    def setex(self, key: str, ttl: int, value: str) -> None:
        raise RuntimeError("setex error")


def create_app_with_cache(dummy_redis: DummyRedis) -> FastAPI:
    app = FastAPI()
    cache_mw.redis_client = dummy_redis  # type: ignore[assignment]
    app.add_middleware(CacheMiddleware, cache_ttl=60)

    @app.get("/items")
    def get_items() -> dict:
        return {"value": "data"}

    return app


def test_cache_middleware_miss_then_hit() -> None:
    dummy = DummyRedis()
    app = create_app_with_cache(dummy)

    with TestClient(app) as client:
        first = client.get("/items")
        assert first.status_code == 200
        assert first.headers["X-Cache"] == "MISS"
        assert first.json() == {"value": "data"}

        second = client.get("/items")
        assert second.status_code == 200
        assert second.headers["X-Cache"] == "HIT"
        assert second.json() == {"value": "data"}


def test_cache_middleware_skips_auth_and_metrics_paths() -> None:
    dummy = DummyRedis()
    app = FastAPI()
    cache_mw.redis_client = dummy  # type: ignore[assignment]
    app.add_middleware(CacheMiddleware, cache_ttl=60)

    @app.get("/auth/login")
    def auth_login() -> dict:
        return {"ok": True}

    @app.get("/metrics")
    def metrics() -> dict:
        return {"ok": True}

    with TestClient(app) as client:
        r1 = client.get("/auth/login")
        r2 = client.get("/metrics")

    assert "X-Cache" not in r1.headers
    assert "X-Cache" not in r2.headers


def test_cache_middleware_marks_error_on_redis_failure() -> None:
    dummy = DummyRedisError()
    app = create_app_with_cache(dummy)

    with TestClient(app) as client:
        response = client.get("/items")

    assert response.status_code == 200
    assert response.headers["X-Cache"] == "ERROR"


def test_cache_invalidation_helpers_use_redis_client() -> None:
    dummy = DummyRedis()
    cache_mw.redis_client = dummy  # type: ignore[assignment]

    dummy.setex("api_cache:foo1", 60, "{}")
    dummy.setex("api_cache:foo2", 60, "{}")

    cache_mw.invalidate_cache("*1*")
    assert "api_cache:foo1" not in dummy.store
    assert "api_cache:foo2" in dummy.store

    cache_mw.clear_all_cache()
    assert dummy.store == {}
