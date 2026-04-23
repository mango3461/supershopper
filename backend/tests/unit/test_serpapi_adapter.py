import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.search.serpapi_adapter import SerpAPIAdapter  # noqa: E402
from app.api.schemas.common import CandidateSeedPayload, SearchQuery, SearchStrategyPayload  # noqa: E402


class _FakeSerpAPIAdapter(SerpAPIAdapter):
    def __init__(self, payloads: dict[str, dict | Exception]) -> None:
        super().__init__(api_key="test-key")
        self._payloads = payloads

    def _call_serpapi(self, search_query: SearchQuery, num: int, engine: str) -> dict:
        del search_query, num
        payload = self._payloads[engine]
        if isinstance(payload, Exception):
            raise payload
        return payload


class SerpAPIAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = SearchStrategyPayload(
            queries=[
                SearchQuery(
                    query="entry mechanical keyboard under 150000 KRW silent switch",
                    rationale="Find beginner-friendly quiet models.",
                )
            ],
            max_products=3,
            strategy_note="test strategy",
        )
        self.candidates = [
            CandidateSeedPayload(
                candidate_id="mk-keymellow-75-flex",
                name="KeyMellow 75 Flex",
                brand="KeyMellow",
                reference_price=149000,
                inferred_layout="75%",
                inferred_switch_type="silent_tactile",
                inferred_noise_level="quiet",
                heuristic_score=0.9,
            ),
            CandidateSeedPayload(
                candidate_id="mk-lumakeys-flow-tkl",
                name="LumaKeys Flow TKL",
                brand="LumaKeys",
                reference_price=129000,
                inferred_layout="TKL",
                inferred_switch_type="silent_linear",
                inferred_noise_level="quiet",
                heuristic_score=0.82,
            ),
        ]

    def test_search_expert_signals_normalizes_live_results(self) -> None:
        adapter = _FakeSerpAPIAdapter(
            {
                "google": {
                    "organic_results": [
                        {
                            "title": "Best beginner mechanical keyboards for quiet offices",
                            "link": "https://example.com/beginner-quiet-keyboards",
                            "source": "Example Reviews",
                            "snippet": "KeyMellow 75 Flex and LumaKeys Flow TKL are often recommended for first-time buyers.",
                        }
                    ]
                }
            }
        )

        signals = adapter.search_expert_signals(self.strategy)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].source, "Example Reviews")
        self.assertIn("KeyMellow 75 Flex", signals[0].mentioned_products)
        self.assertGreater(signals[0].confidence_score, 0.5)

    def test_verify_candidates_normalizes_live_shopping_results(self) -> None:
        adapter = _FakeSerpAPIAdapter(
            {
                "google_shopping": {
                    "shopping_results": [
                        {
                            "title": "KeyMellow 75 Flex mechanical keyboard silent tactile",
                            "product_link": "https://shop.example.com/keymellow-75-flex",
                            "source": "Example Mall",
                            "price": "₩149,000",
                            "extracted_price": 149000,
                            "rating": 4.7,
                            "reviews": 112,
                            "snippet": "Quiet 75% hot swap mechanical keyboard for office use.",
                            "delivery": "free shipping",
                        }
                    ]
                }
            }
        )

        products = adapter.verify_candidates(self.candidates[:1], self.strategy)
        enriched_products = adapter.search_reviews(products, self.strategy)

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "KeyMellow 75 Flex")
        self.assertEqual(products[0].layout, "75%")
        self.assertEqual(products[0].attributes["seller"], "Example Mall")
        self.assertEqual(products[0].attributes["retrieval_source"], "serpapi_live")
        self.assertTrue(products[0].product_id.startswith("serpapi:"))
        self.assertGreater(len(enriched_products[0].evidence), 0)

    def test_verify_candidates_falls_back_to_mock_catalog_when_live_call_fails(self) -> None:
        adapter = _FakeSerpAPIAdapter({"google_shopping": RuntimeError("boom")})

        products = adapter.verify_candidates(self.candidates, self.strategy)

        self.assertGreater(len(products), 0)
        self.assertTrue(products[0].product_id.startswith("keyboard-"))
        self.assertEqual(products[0].attributes["retrieval_source"], "mock_catalog_fallback")


if __name__ == "__main__":
    unittest.main()
