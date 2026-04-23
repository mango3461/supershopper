from app.api.schemas.common import IntentAnalysisPayload, SearchStrategyPayload
from app.domain.models.search_strategy import SearchStrategy
from app.ports.llm_port import LLMPort
from app.ports.logger_port import LoggerPort
from app.prompts.strategy_prompt import render as render_strategy_prompt
from app.services.llm_fallbacks import LLMFallbackService


class BuildSearchStrategyUseCase:
    def __init__(self, llm: LLMPort, fallbacks: LLMFallbackService, logger: LoggerPort) -> None:
        self._llm = llm
        self._fallbacks = fallbacks
        self._logger = logger

    def execute(
        self, intent: IntentAnalysisPayload, max_candidates: int
    ) -> SearchStrategyPayload:
        prompt = render_strategy_prompt(intent)
        strategy = None
        try:
            strategy = self._llm.generate_search_strategy(
                intent,
                prompt,
                max_candidates=max_candidates,
            )
        except Exception as exc:
            self._logger.warning(f"LLM search strategy generation failed, using fallback: {exc}")

        if not self._fallbacks.validate_search_strategy(strategy):
            self._logger.info("Using deterministic fallback for build_search_strategy")
            strategy = self._fallbacks.build_search_strategy(intent, max_candidates)

        _ = SearchStrategy(
            queries=[item.query for item in strategy.queries],
            sources=strategy.sources,
            max_products=strategy.max_products,
        )
        self._logger.debug(f"Built {len(strategy.queries)} search queries")
        return strategy
