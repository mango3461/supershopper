from app.api.schemas.common import IntentAnalysisPayload, UserQueryPayload
from app.domain.models.user_need import UserNeed
from app.ports.llm_port import LLMPort
from app.ports.logger_port import LoggerPort
from app.prompts.intent_prompt import render as render_intent_prompt
from app.services.llm_fallbacks import LLMFallbackService


class AnalyzeIntentUseCase:
    def __init__(self, llm: LLMPort, fallbacks: LLMFallbackService, logger: LoggerPort) -> None:
        self._llm = llm
        self._fallbacks = fallbacks
        self._logger = logger

    def execute(self, user_query: UserQueryPayload) -> IntentAnalysisPayload:
        prompt = render_intent_prompt(user_query.query)
        payload = None
        try:
            payload = self._llm.generate_intent_analysis(user_query, prompt)
        except Exception as exc:
            self._logger.warning(f"LLM intent analysis failed, using fallback: {exc}")

        if not self._fallbacks.validate_intent_analysis(payload):
            self._logger.info("Using deterministic fallback for analyze_intent")
            payload = self._fallbacks.build_intent_analysis(user_query)

        user_need = UserNeed(
            category=payload.category,
            user_level=payload.user_level,
            budget_min=payload.budget.min_price,
            budget_max=payload.budget.max_price,
            constraints=payload.constraints,
            prioritized_attributes=payload.prioritized_attributes,
        )
        self._logger.debug(
            f"Intent analyzed for category={user_need.category}, level={user_need.user_level}"
        )
        return payload
