from app.api.schemas.common import (
    EvidenceFilteringPayload,
    IntentAnalysisPayload,
    RecommendationPayload,
    SummaryPayload,
)
from app.ports.llm_port import LLMPort
from app.ports.logger_port import LoggerPort
from app.prompts.recommendation_prompt import render as render_recommendation_prompt
from app.services.llm_fallbacks import LLMFallbackService
from app.usecases.compare_candidates import CompareCandidatesUseCase


class GenerateRecommendationUseCase:
    def __init__(
        self,
        llm: LLMPort,
        fallbacks: LLMFallbackService,
        compare_candidates_use_case: CompareCandidatesUseCase,
        logger: LoggerPort,
    ) -> None:
        self._llm = llm
        self._fallbacks = fallbacks
        self._compare_candidates = compare_candidates_use_case
        self._logger = logger

    def execute(
        self,
        intent: IntentAnalysisPayload,
        filtered: EvidenceFilteringPayload,
        summary: SummaryPayload,
        max_candidates: int,
    ) -> RecommendationPayload:
        ranked_candidates = self._compare_candidates.execute(filtered.products)
        shortlisted_candidates = ranked_candidates[: max(2, min(max_candidates, 3))]
        recommended_choice = shortlisted_candidates[0] if shortlisted_candidates else None
        prompt = render_recommendation_prompt(intent, summary, shortlisted_candidates)

        wording = None
        try:
            wording = self._llm.generate_recommendation_wording(
                intent=intent,
                shortlisted_candidates=shortlisted_candidates,
                recommended_choice=recommended_choice,
                summary=summary,
                prompt=prompt,
            )
        except Exception as exc:
            self._logger.warning(f"LLM recommendation wording failed, using fallback: {exc}")

        if not self._fallbacks.validate_recommendation_wording(wording):
            self._logger.info("Using deterministic fallback for generate_recommendation")
            wording = self._fallbacks.build_recommendation_wording(
                intent=intent,
                shortlisted_candidates=shortlisted_candidates,
                recommended_choice=recommended_choice,
                summary=summary,
            )

        recommendation = RecommendationPayload(
            interpreted_intent=intent,
            generated_search_queries=filtered.strategy.queries,
            buying_guide_summary=summary,
            top_candidates=shortlisted_candidates,
            recommended_choice=recommended_choice,
            recommendation_reason=wording.recommendation_reason,
            caution_or_uncertainty=wording.caution_or_uncertainty,
        )
        self._logger.debug(
            f"Generated recommendation with {len(recommendation.top_candidates)} products"
        )
        return recommendation
