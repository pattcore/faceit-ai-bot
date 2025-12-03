import pytest

from src.server.services.cache_service import CacheService


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:  # type: ignore[override]
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:  # type: ignore[override]
        # TTL is ignored in the dummy implementation
        self.store[key] = value

    async def delete(self, key: str) -> int:  # type: ignore[override]
        self.store.pop(key, None)
        return 1

    async def exists(self, key: str) -> int:  # type: ignore[override]
        return 1 if key in self.store else 0


class DummyRedisError(DummyRedis):
    async def setex(self, key: str, ttl: int, value: str) -> None:  # type: ignore[override]
        raise RuntimeError("setex error")

    async def delete(self, key: str) -> int:  # type: ignore[override]
        raise RuntimeError("delete error")

    async def exists(self, key: str) -> int:  # type: ignore[override]
        raise RuntimeError("exists error")


@pytest.mark.asyncio
async def test_get_returns_none_when_disabled() -> None:
    service = CacheService()
    service.enabled = False
    service.redis_client = None

    result = await service.get("some-key")
    assert result is None


@pytest.mark.asyncio
async def test_get_miss_and_hit_with_labels() -> None:
    service = CacheService()
    service.redis_client = DummyRedis()
    service.enabled = True

    # Miss path
    result = await service.get("unknown-key")
    assert result is None

    # Hit path with different prefixes -> different cache labels in metrics
    service.redis_client.store["player:analysis:test"] = "{\"foo\": 1}"
    service.redis_client.store["player:stats:test"] = "{\"bar\": 2}"

    result_analysis = await service.get("player:analysis:test")
    result_stats = await service.get("player:stats:test")

    assert result_analysis == {"foo": 1}
    assert result_stats == {"bar": 2}


@pytest.mark.asyncio
async def test_set_success_and_error_paths() -> None:
    service = CacheService()
    service.enabled = True

    # Successful set
    dummy = DummyRedis()
    service.redis_client = dummy

    ok = await service.set("key1", {"a": 1}, ttl=10)
    assert ok is True
    assert "key1" in dummy.store

    # Error path
    service.redis_client = DummyRedisError()
    failed = await service.set("key2", {"b": 2}, ttl=10)
    assert failed is False


@pytest.mark.asyncio
async def test_delete_and_exists_paths() -> None:
    service = CacheService()
    dummy = DummyRedis()
    service.redis_client = dummy
    service.enabled = True

    dummy.store["k"] = "{}"
    assert await service.exists("k") is True

    deleted = await service.delete("k")
    assert deleted is True
    assert await service.exists("k") is False


@pytest.mark.asyncio
async def test_delete_and_exists_error_paths() -> None:
    service = CacheService()
    service.redis_client = DummyRedisError()
    service.enabled = True

    # Errors should be swallowed and reported as False
    deleted = await service.delete("k")
    assert deleted is False
    assert await service.exists("k") is False


def test_cache_key_helpers() -> None:
    service = CacheService()

    assert (
        service.get_player_cache_key("NickName")
        == "player:analysis:v2:nickname"
    )
    assert (
        service.get_stats_cache_key("NickName")
        == "player:stats:nickname"
    )
