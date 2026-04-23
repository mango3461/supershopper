import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.schemas.common import (  # noqa: E402
    EvidenceFilteringPayload,
    IntentAnalysisPayload,
    SearchStrategyPayload,
    SummaryPayload,
    UserQueryPayload,
)
from app.ports.llm_port import LLMPort  # noqa: E402
from app.ports.logger_port import LoggerPort  # noqa: E402
from app.services.llm_fallbacks import LLMFallbackService  # noqa: E402
from app.usecases.analyze_intent import AnalyzeIntentUseCase  # noqa: E402
from app.usecases.build_search_strategy import BuildSearchStrategyUseCase  # noqa: E402
from app.usecases.compare_candidates import CompareCandidatesUseCase  # noqa: E402
from app.usecases.generate_recommendation import GenerateRecommendationUseCase  # noqa: E402


class NullLogger(LoggerPort):
    def debug(self, message: str) -> None:
        del message

    def info(self, message: str) -> None:
        del message

    def warning(self, message: str) -> None:
        del message

    def error(self, message: str) -> None:
        del message


class FailingLLMStub(LLMPort):
    provider_name = "failing-llm"
    mode = "mock"

    def generate_intent_analysis(self, user_query: UserQueryPayload, prompt: str):
        del user_query, prompt
        raise RuntimeError("intent unavailable")

    def generate_search_strategy(
        self, intent: IntentAnalysisPayload, prompt: str, max_candidates: int
    ):
        del intent, prompt, max_candidates
        return SearchStrategyPayload(queries=[])

    def generate_buying_guide_summary(
        self, intent: IntentAnalysisPayload, filtered: EvidenceFilteringPayload, prompt: str
    ):
        del intent, filtered, prompt
        return SummaryPayload(summary="", beginner_tip="", tradeoff_note="")

    def generate_recommendation_wording(
        self,
        intent: IntentAnalysisPayload,
        shortlisted_candidates,
        recommended_choice,
        summary: SummaryPayload,
        prompt: str,
    ):
        del intent, shortlisted_candidates, recommended_choice, summary, prompt
        return None


class LLMFallbackUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = FailingLLMStub()
        self.logger = NullLogger()
        self.fallbacks = LLMFallbackService()

    def test_analyze_intent_falls_back_when_llm_fails(self) -> None:
        usecase = AnalyzeIntentUseCase(self.llm, self.fallbacks, self.logger)

        result = usecase.execute(
            UserQueryPayload(
                query="처음 사는 기계식 키보드 추천해줘. 시끄럽지 않았으면 좋겠고 15만 원 이하면 좋겠어."
            )
        )

        self.assertEqual(result.category, "mechanical_keyboard")
        self.assertEqual(result.budget.max_price, 150000)
        self.assertEqual(result.preferred_noise_level, "quiet")

    def test_build_search_strategy_falls_back_when_llm_returns_invalid_payload(self) -> None:
        analyze = AnalyzeIntentUseCase(self.llm, self.fallbacks, self.logger)
        intent = analyze.execute(UserQueryPayload(query="기계식 키보드 추천해줘"))
        usecase = BuildSearchStrategyUseCase(self.llm, self.fallbacks, self.logger)

        strategy = usecase.execute(intent, max_candidates=3)

        self.assertGreaterEqual(len(strategy.queries), 3)
        self.assertTrue(strategy.strategy_note)

    def test_recommendation_wording_falls_back_when_llm_returns_none(self) -> None:
        fallback_intent = self.fallbacks.build_intent_analysis(
            UserQueryPayload(query="추천 좀 해줘.")
        )
        fallback_strategy = self.fallbacks.build_search_strategy(fallback_intent, 2)
        filtered = EvidenceFilteringPayload(strategy=fallback_strategy, products=[])
        summary = self.fallbacks.build_buying_guide_summary(fallback_intent, filtered)

        usecase = GenerateRecommendationUseCase(
            self.llm,
            self.fallbacks,
            CompareCandidatesUseCase(self.logger),
            self.logger,
        )

        recommendation = usecase.execute(
            intent=fallback_intent,
            filtered=filtered,
            summary=summary,
            max_candidates=2,
        )

        self.assertIsNone(recommendation.recommended_choice)
        self.assertIn("찾지 못했습니다", recommendation.recommendation_reason)
        self.assertGreater(len(recommendation.caution_or_uncertainty), 0)


if __name__ == "__main__":
    unittest.main()
