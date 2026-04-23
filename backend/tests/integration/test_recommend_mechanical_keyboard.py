import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402


class RecommendMechanicalKeyboardIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_recommend_returns_beginner_keyboard_shortlist(self) -> None:
        response = self.client.post(
            "/recommend",
            json={
                "query": "처음 사는 기계식 키보드 추천해줘. 시끄럽지 않았으면 좋겠고 15만 원 이하면 좋겠어.",
                "max_candidates": 3,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["interpreted_intent"]["category"], "mechanical_keyboard")
        self.assertEqual(payload["interpreted_intent"]["user_level"], "beginner")
        self.assertEqual(payload["interpreted_intent"]["budget"]["max_price"], 150000)
        self.assertEqual(payload["interpreted_intent"]["preferred_noise_level"], "quiet")
        self.assertGreaterEqual(len(payload["generated_search_queries"]), 3)
        self.assertTrue(2 <= len(payload["top_candidates"]) <= 3)
        self.assertEqual(payload["recommended_choice"]["name"], "KeyMellow 75 Flex")
        self.assertGreater(len(payload["caution_or_uncertainty"]), 0)
        self.assertGreater(len(payload["debug"]["expert_signals"]), 0)
        self.assertGreater(len(payload["debug"]["generated_candidates"]), 0)
        self.assertIn(
            payload["debug"]["expert_signal_source_mode"],
            {"live", "fallback", "mixed", "unknown"},
        )
        self.assertTrue(
            payload["debug"]["generated_candidates"][0]["candidate_source_reason"]
        )
        self.assertEqual(
            payload["workflow"]["workflow_order"],
            [
                "analyze_intent",
                "build_search_strategy",
                "retrieve_expert_signals",
                "generate_candidates",
                "retrieve_products",
                "filter_evidence",
                "summarize_results",
                "generate_recommendation",
            ],
        )

    def test_recommend_returns_empty_shortlist_when_budget_is_too_low(self) -> None:
        response = self.client.post(
            "/recommend",
            json={
                "query": "처음 사는 기계식 키보드 추천해줘. 조용했으면 좋겠고 5만 원 이하면 좋겠어.",
                "max_candidates": 3,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["top_candidates"], [])
        self.assertIsNone(payload["recommended_choice"])
        self.assertIn("찾지 못", payload["recommendation_reason"])
        self.assertGreater(len(payload["caution_or_uncertainty"]), 1)
        self.assertGreater(len(payload["debug"]["generated_candidates"]), 0)

    def test_recommend_handles_ambiguous_input_with_default_beginner_assumptions(self) -> None:
        response = self.client.post(
            "/recommend",
            json={
                "query": "추천 좀 해줘.",
                "max_candidates": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["interpreted_intent"]["category"], "mechanical_keyboard")
        self.assertLess(payload["interpreted_intent"]["confidence_score"], 0.75)
        self.assertEqual(len(payload["top_candidates"]), 2)
        self.assertGreater(len(payload["debug"]["expert_signals"]), 0)


if __name__ == "__main__":
    unittest.main()
