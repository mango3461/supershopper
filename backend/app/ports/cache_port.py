from abc import ABC, abstractmethod
from typing import Any


class CachePort(ABC):
    provider_name: str
    mode: str

    @abstractmethod
    def get(self, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError

