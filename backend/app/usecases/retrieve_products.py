from app.api.schemas.common import CandidateGenerationPayload, RetrievalPayload
from app.ports.cache_port import CachePort
from app.ports.logger_port import LoggerPort
from app.ports.search_port import SearchPort


class RetrieveProductsUseCase:
    def __init__(self, search: SearchPort, cache: CachePort, logger: LoggerPort) -> None:
        self._search = search
        self._cache = cache
        self._logger = logger

    def execute(self, candidate_generation: CandidateGenerationPayload) -> RetrievalPayload:
        strategy = candidate_generation.strategy
        candidate_ids = "|".join(item.candidate_id for item in candidate_generation.candidates)
        cache_key = f"candidate-verification:{'|'.join(item.query for item in strategy.queries)}:{candidate_ids}"
        cached_payload = self._cache.get(cache_key)
        if isinstance(cached_payload, RetrievalPayload):
            self._logger.debug("Loaded retrieval payload from cache")
            return cached_payload

        products = self._search.verify_candidates(candidate_generation.candidates, strategy)
        enriched_products = self._search.search_reviews(products, strategy)
        payload = RetrievalPayload(strategy=strategy, products=enriched_products)
        self._cache.set(cache_key, payload, ttl_seconds=300)
        self._logger.debug(f"Verified {len(payload.products)} candidate products")
        return payload
