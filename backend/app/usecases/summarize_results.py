from app.api.schemas.common import EvidenceFilteringPayload, IntentAnalysisPayload, SummaryPayload
from app.ports.llm_port import LLMPort
from app.ports.logger_port import LoggerPort
from app.prompts.summary_prompt import render as render_summary_prompt
from app.services.llm_fallbacks import LLMFallbackService


class SummarizeResultsUseCase:
    def __init__(self, llm: LLMPort, fallbacks: LLMFallbackService, logger: LoggerPort) -> None:
        self._llm = llm
        self._fallbacks = fallbacks
        self._logger = logger

    def execute(
        self, intent: IntentAnalysisPayload, filtered: EvidenceFilteringPayload
    ) -> SummaryPayload:
        prompt = render_summary_prompt(intent, filtered)
        summary = None
        try:
            summary = self._llm.generate_buying_guide_summary(intent, filtered, prompt)
        except Exception as exc:
            self._logger.warning(f"LLM summary generation failed, using fallback: {exc}")

        if not self._fallbacks.validate_buying_guide_summary(summary):
            self._logger.info("Using deterministic fallback for summarize_results")
            summary = self._fallbacks.build_buying_guide_summary(intent, filtered)

        self._logger.debug("Generated summary payload")
        return summary
