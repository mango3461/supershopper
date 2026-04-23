from abc import ABC, abstractmethod

from app.api.schemas.common import (
    CandidateSeedPayload,
    ExpertSignalPayload,
    ProductPayload,
    SearchStrategyPayload,
)


class SearchPort(ABC):
    provider_name: str
    mode: str

    @abstractmethod
    def search_expert_signals(self, strategy: SearchStrategyPayload) -> list[ExpertSignalPayload]:
        raise NotImplementedError

    @abstractmethod
    def verify_candidates(
        self,
        candidates: list[CandidateSeedPayload],
        strategy: SearchStrategyPayload,
    ) -> list[ProductPayload]:
        raise NotImplementedError

    @abstractmethod
    def search_reviews(
        self, products: list[ProductPayload], strategy: SearchStrategyPayload
    ) -> list[ProductPayload]:
        raise NotImplementedError
