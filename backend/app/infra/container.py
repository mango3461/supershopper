from functools import lru_cache
import os
import logging

from app.adapters.cache.redis_adapter import MockCacheAdapter, RedisAdapter
from app.adapters.llm.gemini_adapter import GeminiAdapter
from app.adapters.llm.openai_adapter import MockLLMAdapter, OpenAIAdapter
from app.adapters.logging.app_logger import AppLogger
from app.adapters.search.serpapi_adapter import MockSearchAdapter, SerpAPIAdapter
from app.api.schemas.common import ProviderStatusPayload
from app.infra.config import is_configured
from app.infra.settings import get_settings
from app.orchestrators.shopping_flow import ShoppingFlowOrchestrator
from app.services.llm_fallbacks import LLMFallbackService
from app.services.response_formatter import ResponseFormatter
from app.usecases.analyze_intent import AnalyzeIntentUseCase
from app.usecases.build_search_strategy import BuildSearchStrategyUseCase
from app.usecases.compare_candidates import CompareCandidatesUseCase
from app.usecases.filter_evidence import FilterEvidenceUseCase
from app.usecases.generate_candidates import GenerateCandidatesUseCase
from app.usecases.generate_recommendation import GenerateRecommendationUseCase
from app.usecases.retrieve_expert_signals import RetrieveExpertSignalsUseCase
from app.usecases.retrieve_products import RetrieveProductsUseCase
from app.usecases.summarize_results import SummarizeResultsUseCase


class AppContainer:
    def __init__(self) -> None:
        settings = get_settings()

        self.logger = AppLogger()
        self._bootstrap_logger = logging.getLogger("supershopper.bootstrap")
        self.llm = self._build_llm(settings.llm_provider, settings.openai_api_key, settings.google_api_key)
        self.search = self._build_search(settings.search_provider, settings.serpapi_api_key)
        self.cache = self._build_cache(settings.cache_provider, settings.redis_url)
        self._bootstrap_logger.info(
            "LLM provider setting=%s google_key_loaded=%s search_provider=%s serpapi_key_loaded=%s selected_llm_adapter=%s selected_search_adapter=%s",
            settings.llm_provider,
            bool(settings.google_api_key),
            settings.search_provider,
            bool(settings.serpapi_api_key),
            type(self.llm).__name__,
            type(self.search).__name__,
        )

        self.llm_fallbacks = LLMFallbackService()
        self.response_formatter = ResponseFormatter()

        self.analyze_intent = AnalyzeIntentUseCase(self.llm, self.llm_fallbacks, self.logger)
        self.build_search_strategy = BuildSearchStrategyUseCase(
            self.llm,
            self.llm_fallbacks,
            self.logger,
        )
        self.retrieve_expert_signals = RetrieveExpertSignalsUseCase(self.search, self.cache, self.logger)
        self.generate_candidates = GenerateCandidatesUseCase(self.logger)
        self.retrieve_products = RetrieveProductsUseCase(self.search, self.cache, self.logger)
        self.filter_evidence = FilterEvidenceUseCase(self.logger)
        self.summarize_results = SummarizeResultsUseCase(
            self.llm,
            self.llm_fallbacks,
            self.logger,
        )
        self.compare_candidates = CompareCandidatesUseCase(self.logger)
        self.generate_recommendation = GenerateRecommendationUseCase(
            self.llm,
            self.llm_fallbacks,
            self.compare_candidates,
            self.logger,
        )

        self.shopping_flow = ShoppingFlowOrchestrator(
            analyze_intent_use_case=self.analyze_intent,
            build_search_strategy_use_case=self.build_search_strategy,
            retrieve_expert_signals_use_case=self.retrieve_expert_signals,
            generate_candidates_use_case=self.generate_candidates,
            retrieve_products_use_case=self.retrieve_products,
            filter_evidence_use_case=self.filter_evidence,
            summarize_results_use_case=self.summarize_results,
            generate_recommendation_use_case=self.generate_recommendation,
            logger=self.logger,
            providers=self.provider_status(),
        )

    def provider_status(self) -> ProviderStatusPayload:
        return ProviderStatusPayload(
            llm=self.llm.mode,
            search=self.search.mode,
            cache=self.cache.mode,
        )

    @staticmethod
    def _build_llm(provider: str, openai_api_key: str | None, google_api_key: str | None):
        if provider == "openai" and is_configured(openai_api_key):
            return OpenAIAdapter(
                api_key=openai_api_key,
                model=os.getenv("OPENAI_INTENT_MODEL", "gpt-4.1-mini"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            )
        if provider == "gemini" and is_configured(google_api_key):
            return GeminiAdapter(
                api_key=google_api_key,
                model=os.getenv("GEMINI_SEARCH_MODEL", "gemini-2.5-flash"),
                base_url=os.getenv(
                    "GEMINI_BASE_URL",
                    "https://generativelanguage.googleapis.com/v1",
                ),
            )
        return MockLLMAdapter()

    @staticmethod
    def _build_search(provider: str, serpapi_api_key: str | None):
        settings = get_settings()
        if provider == "serpapi" and is_configured(serpapi_api_key):
            return SerpAPIAdapter(
                api_key=serpapi_api_key,
                engine=settings.serpapi_engine,
                expert_engine=settings.serpapi_expert_engine,
                base_url=settings.serpapi_base_url,
                google_domain=settings.serpapi_google_domain,
                gl=settings.serpapi_gl,
                hl=settings.serpapi_hl,
                device=settings.serpapi_device,
                location=settings.serpapi_location,
                num=settings.serpapi_num,
                timeout_seconds=settings.serpapi_timeout_seconds,
            )
        return MockSearchAdapter()

    @staticmethod
    def _build_cache(provider: str, redis_url: str | None):
        if provider == "redis" and is_configured(redis_url):
            return RedisAdapter()
        return MockCacheAdapter()


@lru_cache
def get_container() -> AppContainer:
    return AppContainer()
