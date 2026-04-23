import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.schemas.common import (  # noqa: E402
    ExpertSignalPayload,
    ExpertSignalsPayload,
    IntentAnalysisPayload,
    SearchQuery,
    SearchStrategyPayload,
)
from app.ports.logger_port import LoggerPort  # noqa: E402
from app.usecases.generate_candidates import GenerateCandidatesUseCase  # noqa: E402


class NullLogger(LoggerPort):
    def debug(self, message: str) -> None:
        del message

    def info(self, message: str) -> None:
        del message

    def warning(self, message: str) -> None:
        del message

    def error(self, message: str) -> None:
        del message


class GenerateCandidatesUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.usecase = GenerateCandidatesUseCase(NullLogger())
        self.intent = IntentAnalysisPayload(
            original_query="처음 사는 기계식 키보드 추천해줘. 조용했으면 좋겠고 15만 원 이하였으면 좋겠어.",
            budget={"currency": "KRW", "max_price": 150000},
            preferred_noise_level="quiet",
            preferred_key_feel="silent_linear_or_tactile",
            preferred_layout="undecided",
        )
        self.strategy = SearchStrategyPayload(
            queries=[
                SearchQuery(
                    query="입문용 기계식 키보드 15만 원 이하 저소음 적축 또는 저소음 갈축 추천",
                    rationale="예산 안에서 조용한 입문용 모델을 찾습니다.",
                )
            ],
            max_products=5,
            strategy_note="test strategy",
        )

    def test_generate_candidates_marks_live_signal_reason(self) -> None:
        expert_signals = ExpertSignalsPayload(
            strategy=self.strategy,
            signals=[
                ExpertSignalPayload(
                    signal_id="sig-1",
                    title="Best beginner mechanical keyboards",
                    source="Example Reviews",
                    snippet="KeyMellow 75 Flex and LumaKeys Flow TKL are reliable quiet picks.",
                    mentioned_products=["KeyMellow 75 Flex", "LumaKeys Flow TKL"],
                    confidence_score=0.8,
                    retrieval_source="serpapi_live",
                )
            ],
        )

        result = self.usecase.execute(self.intent, expert_signals, max_candidates=3)

        self.assertGreater(len(result.candidates), 0)
        self.assertEqual(result.candidates[0].source_signal_mode, "live")
        self.assertTrue(result.candidates[0].candidate_source_reason)
        self.assertGreater(len(result.candidates[0].source_signal_titles), 0)

    def test_generate_candidates_marks_fallback_signal_reason(self) -> None:
        expert_signals = ExpertSignalsPayload(
            strategy=self.strategy,
            signals=[
                ExpertSignalPayload(
                    signal_id="sig-2",
                    title="입문용 저소음 기계식 키보드 추천",
                    source="mock-expert-guide",
                    snippet="KeyMellow 75 Flex와 LumaKeys Flow TKL이 자주 언급됩니다.",
                    mentioned_products=["KeyMellow 75 Flex", "LumaKeys Flow TKL"],
                    confidence_score=0.7,
                    retrieval_source="mock_expert_signal_fallback",
                    fallback_reason="serpapi_error",
                )
            ],
        )

        result = self.usecase.execute(self.intent, expert_signals, max_candidates=3)

        self.assertGreater(len(result.candidates), 0)
        self.assertEqual(result.candidates[0].source_signal_mode, "fallback")
        self.assertIn("fallback", result.candidates[0].candidate_source_reason)


if __name__ == "__main__":
    unittest.main()
