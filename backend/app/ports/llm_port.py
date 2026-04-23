from abc import ABC, abstractmethod

from app.api.schemas.common import (
    EvidenceFilteringPayload,
    IntentAnalysisPayload,
    ProductPayload,
    RecommendationWordingPayload,
    SearchStrategyPayload,
    SummaryPayload,
    UserQueryPayload,
)


class LLMPort(ABC):
    provider_name: str
    mode: str

    @abstractmethod
    def generate_intent_analysis(
        self, user_query: UserQueryPayload, prompt: str
    ) -> IntentAnalysisPayload | None:
        raise NotImplementedError

    @abstractmethod
    def generate_search_strategy(
        self, intent: IntentAnalysisPayload, prompt: str, max_candidates: int
    ) -> SearchStrategyPayload | None:
        raise NotImplementedError

    @abstractmethod
    def generate_buying_guide_summary(
        self, intent: IntentAnalysisPayload, filtered: EvidenceFilteringPayload, prompt: str
    ) -> SummaryPayload | None:
        raise NotImplementedError

    @abstractmethod
    def generate_recommendation_wording(
        self,
        intent: IntentAnalysisPayload,
        shortlisted_candidates: list[ProductPayload],
        recommended_choice: ProductPayload | None,
        summary: SummaryPayload,
        prompt: str,
    ) -> RecommendationWordingPayload | None:
        raise NotImplementedError
