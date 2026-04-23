from app.api.schemas.common import ExpertSignalsPayload, SearchStrategyPayload
from app.ports.cache_port import CachePort
from app.ports.logger_port import LoggerPort
from app.ports.search_port import SearchPort


class RetrieveExpertSignalsUseCase:
    def __init__(self, search: SearchPort, cache: CachePort, logger: LoggerPort) -> None:
        self._search = search
        self._cache = cache
        self._logger = logger

    def execute(self, strategy: SearchStrategyPayload) -> ExpertSignalsPayload:
        cache_key = f"expert-signals:{'|'.join(item.query for item in strategy.queries)}"
        cached_payload = self._cache.get(cache_key)
        if isinstance(cached_payload, ExpertSignalsPayload):
            self._logger.debug("Loaded expert signals payload from cache")
            return cached_payload

        signals = self._search.search_expert_signals(strategy)
        payload = ExpertSignalsPayload(strategy=strategy, signals=signals)
        self._cache.set(cache_key, payload, ttl_seconds=300)
        self._logger.debug(f"Retrieved {len(payload.signals)} expert signals")
        return payload
