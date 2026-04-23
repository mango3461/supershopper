from typing import Any

from app.ports.cache_port import CachePort


class MockCacheAdapter(CachePort):
    provider_name = "mock-cache"
    mode = "mock"

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        del ttl_seconds
        self._store[key] = value


class RedisAdapter(MockCacheAdapter):
    provider_name = "redis"
    mode = "configured"

