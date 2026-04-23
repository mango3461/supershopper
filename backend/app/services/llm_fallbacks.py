import re

from app.api.schemas.common import (
    BudgetPayload,
    EvidenceFilteringPayload,
    IntentAnalysisPayload,
    ProductPayload,
    RecommendationWordingPayload,
    SearchQuery,
    SearchStrategyPayload,
    SummaryPayload,
    UserQueryPayload,
)


QUIET_TOKENS = ["시끄럽지", "조용", "저소음", "quiet", "noise"]
BEGINNER_TOKENS = ["처음", "입문", "first", "beginner"]
KEYBOARD_TOKENS = ["키보드", "기계식", "keyboard"]
SWITCH_TOKENS = ["적축", "갈축", "청축", "저소음", "linear", "tactile", "clicky"]
LAYOUT_TOKENS = ["75%", "75배열", "tkl", "tenkeyless", "텐키리스", "풀배열"]


class LLMFallbackService:
    def build_intent_analysis(self, user_query: UserQueryPayload) -> IntentAnalysisPayload:
        query = user_query.query
        budget_max = (
            int(user_query.budget_max)
            if user_query.budget_max is not None
            else self._extract_budget_krw(query)
        )
        budget_min = int(user_query.budget_min) if user_query.budget_min is not None else None
        noise_preference = "quiet" if self._contains_any(query, QUIET_TOKENS) else "undecided"
        user_level = "beginner" if self._contains_any(query, BEGINNER_TOKENS) else "intermediate"
        preferred_layout = self._detect_layout_preference(query)
        preferred_key_feel = self._detect_key_feel(query, noise_preference)
        is_ambiguous_request = self._is_ambiguous_request(query, budget_max, noise_preference)

        constraints = list(user_query.constraints)
        if noise_preference == "quiet":
            constraints.append("공용 공간에서도 부담이 적은 조용한 키보드가 적합합니다.")
        if budget_max is not None:
            constraints.append(f"예산은 {budget_max:,}원 이하로 맞추는 것이 좋습니다.")
        if is_ambiguous_request:
            constraints.append("입력 정보가 부족해 입문용 기계식 키보드 기본 시나리오로 해석했습니다.")

        if is_ambiguous_request:
            interpretation_summary = (
                "요청 정보가 다소 모호해 입문용 기계식 키보드 기본 시나리오로 해석했습니다. "
                "우선은 조용한 스위치, 무난한 배열, 과하지 않은 가격대를 기준으로 후보를 좁힙니다."
            )
            confidence_score = 0.62
        else:
            interpretation_summary = (
                "처음 사는 기계식 키보드를 찾고 있으며, 소음은 낮고 예산은 무리하지 않은 선에서 "
                "맞추고 싶은 요청으로 해석했습니다."
            )
            confidence_score = 0.96 if self._contains_any(query, KEYBOARD_TOKENS) else 0.84

        return IntentAnalysisPayload(
            original_query=query,
            category="mechanical_keyboard",
            category_label="Mechanical Keyboard",
            user_level=user_level,
            use_case="First mechanical keyboard for daily typing and general use.",
            budget=BudgetPayload(
                currency="KRW",
                min_price=budget_min,
                max_price=budget_max,
            ),
            constraints=constraints,
            prioritized_attributes=["noise", "key feel", "layout", "price"],
            preferred_noise_level=noise_preference,
            preferred_key_feel=preferred_key_feel,
            preferred_layout=preferred_layout,
            desired_features=[
                "조용한 스위치 성향",
                "기본 상태에서도 무난한 안정성",
                "입문자가 적응하기 쉬운 배열",
                "예산 안에서 납득 가능한 가성비",
            ],
            comparison_axes=["noise", "key feel", "layout", "price"],
            interpretation_summary=interpretation_summary,
            confidence_score=confidence_score,
        )

    def build_search_strategy(
        self, intent: IntentAnalysisPayload, max_candidates: int
    ) -> SearchStrategyPayload:
        budget_text = (
            f"{int(intent.budget.max_price / 10000)}만 원 이하"
            if intent.budget.max_price is not None
            else "입문용"
        )
        layout_hint = (
            "75배열"
            if intent.preferred_layout == "75%"
            else "텐키리스"
            if intent.preferred_layout == "TKL"
            else "75배열 또는 텐키리스"
        )
        switch_hint = (
            "저소음 적축"
            if intent.preferred_key_feel == "silent_linear"
            else "저소음 갈축"
            if intent.preferred_key_feel == "silent_tactile"
            else "저소음 적축 또는 저소음 갈축"
        )
        queries = [
            SearchQuery(
                query=f"입문용 기계식 키보드 {budget_text} {switch_hint} 추천",
                rationale="예산 안에서 조용한 입문용 모델을 찾습니다.",
            ),
            SearchQuery(
                query=f"기계식 키보드 {switch_hint} 차이 입문 가이드",
                rationale="처음 쓰는 사람에게 무난한 스위치 차이를 정리합니다.",
            ),
            SearchQuery(
                query=f"기계식 키보드 {layout_hint} 조용한 모델 비교",
                rationale="입문자가 적응하기 쉬운 배열을 비교합니다.",
            ),
            SearchQuery(
                query="처음 사는 기계식 키보드 핫스왑 스테빌라이저 체크 포인트",
                rationale="초보자가 놓치기 쉬운 기본 체크 포인트를 확인합니다.",
            ),
        ]
        return SearchStrategyPayload(
            queries=queries[: max(3, min(max_candidates + 1, 4))],
            sources=["shopping_search", "review_search"],
            max_products=max(max_candidates + 2, 4),
            strategy_note=(
                "먼저 조용하고 입문자에게 무난한 모델을 넓게 찾고, "
                "그다음 배열과 가격 차이로 후보를 줄이는 방식으로 검색 전략을 구성했습니다."
            ),
        )

    def build_buying_guide_summary(
        self, intent: IntentAnalysisPayload, filtered: EvidenceFilteringPayload
    ) -> SummaryPayload:
        top_names = ", ".join(product.name for product in filtered.products[:3]) or "후보 없음"
        budget_text = (
            f"{intent.budget.max_price:,}원 이하"
            if intent.budget.max_price is not None
            else "예산 정보 없음"
        )
        source_note = self._build_source_note(filtered.products)

        if not filtered.products:
            return SummaryPayload(
                summary=f"현재 조건으로는 {budget_text} 범위에서 추천할 만한 후보를 찾지 못했습니다.",
                comparison_points=[
                    "예산이 너무 낮으면 저소음 스위치 기반 모델 선택지가 크게 줄어듭니다.",
                    "소음, 배열, 무선 여부 중 하나를 완화하면 다시 후보가 늘어날 수 있습니다.",
                ],
                beginner_tip=(
                    "처음 구매라면 저소음 스위치를 우선으로 보되, 예산을 조금만 올려도 선택지가 크게 넓어집니다."
                ),
                tradeoff_note=source_note,
            )

        return SummaryPayload(
            summary=(
                f"처음 사는 기계식 키보드라면 {budget_text} 범위에서 조용한 스위치와 무난한 배열을 "
                f"우선으로 보는 것이 안전합니다. 현재 추린 후보는 {top_names}입니다."
            ),
            comparison_points=[
                "저소음 적축은 가장 무난하게 조용하고 부드러운 편입니다.",
                "저소음 갈축은 소음을 줄이면서도 약한 구분감을 남겨 처음 쓰기 편한 경우가 많습니다.",
                "75% 배열은 공간 활용이 좋고, 텐키리스는 적응이 쉬운 편입니다.",
                "같은 가격대에서는 RGB보다 스테빌라이저 상태와 핫스왑 여부가 더 중요할 수 있습니다.",
            ],
            beginner_tip="키감 취향이 아직 확실하지 않다면 청축보다 저소음 적축이나 저소음 갈축부터 시작하는 편이 안전합니다.",
            tradeoff_note=source_note,
        )

    def build_recommendation_wording(
        self,
        intent: IntentAnalysisPayload,
        shortlisted_candidates: list[ProductPayload],
        recommended_choice: ProductPayload | None,
        summary: SummaryPayload,
    ) -> RecommendationWordingPayload:
        if recommended_choice is not None:
            recommendation_reason = (
                f"{recommended_choice.name}를 최종 추천한 이유는 예산 안에서 소음 조건을 맞추고, "
                f"처음 쓰는 사람이 적응하기 쉬운 구성일 가능성이 높기 때문입니다."
            )
        else:
            recommendation_reason = "현재 조건을 모두 만족하는 기계식 키보드 후보를 찾지 못했습니다."

        caution_or_uncertainty = [summary.tradeoff_note]
        if intent.confidence_score < 0.75:
            caution_or_uncertainty.append("입력 정보가 모호해 입문용 기본 조건을 기준으로 추천했습니다.")
        if intent.preferred_layout == "undecided":
            caution_or_uncertainty.append("배열 선호가 불분명해 75% 배열과 텐키리스를 우선 후보로 보았습니다.")
        if any(product.switch_type == "silent_linear" for product in shortlisted_candidates):
            caution_or_uncertainty.append("저소음 적축은 조용하지만 저소음 갈축보다 키압 구분감이 더 약하게 느껴질 수 있습니다.")
        if any(self._candidate_uses_mock_source(product) for product in shortlisted_candidates):
            caution_or_uncertainty.append("일부 후보는 live 검색 결과가 부족해 mock fallback 데이터로 보강되었습니다.")
        if not shortlisted_candidates:
            caution_or_uncertainty.append("예산을 조금 올리거나 소음 조건을 완화하면 후보가 다시 늘어날 수 있습니다.")

        return RecommendationWordingPayload(
            recommendation_reason=recommendation_reason,
            caution_or_uncertainty=caution_or_uncertainty,
        )

    def validate_intent_analysis(self, payload: IntentAnalysisPayload | None) -> bool:
        if payload is None:
            return False
        return bool(
            payload.category == "mechanical_keyboard"
            and payload.interpretation_summary.strip()
            and payload.prioritized_attributes
        )

    def validate_search_strategy(self, payload: SearchStrategyPayload | None) -> bool:
        if payload is None:
            return False
        return bool(payload.queries and 1 <= payload.max_products <= 10)

    def validate_buying_guide_summary(self, payload: SummaryPayload | None) -> bool:
        if payload is None:
            return False
        return bool(payload.summary.strip() and payload.beginner_tip.strip() and payload.tradeoff_note.strip())

    def validate_recommendation_wording(
        self, payload: RecommendationWordingPayload | None
    ) -> bool:
        if payload is None:
            return False
        return bool(payload.recommendation_reason.strip())

    @staticmethod
    def _contains_any(query: str, keywords: list[str]) -> bool:
        normalized = query.lower()
        return any(keyword in normalized for keyword in keywords)

    @staticmethod
    def _extract_budget_krw(raw_query: str) -> int | None:
        ten_thousand_won = re.search(r"(\d+(?:\.\d+)?)\s*만\s*원?", raw_query)
        if ten_thousand_won:
            return int(float(ten_thousand_won.group(1)) * 10000)

        won = re.search(r"(\d[\d,]*)\s*원", raw_query)
        if won:
            return int(won.group(1).replace(",", ""))

        return None

    def _detect_layout_preference(self, query: str) -> str:
        if self._contains_any(query, ["75%", "75배열"]):
            return "75%"
        if self._contains_any(query, ["tkl", "tenkeyless", "텐키리스"]):
            return "TKL"
        if self._contains_any(query, ["full size", "full-size", "풀배열", "104키", "108키"]):
            return "full_size"
        return "undecided"

    def _detect_key_feel(self, query: str, noise_preference: str) -> str:
        normalized = query.lower()
        if "저소음 적축" in normalized:
            return "silent_linear"
        if "저소음 갈축" in normalized:
            return "silent_tactile"
        if "적축" in normalized:
            return "linear"
        if "갈축" in normalized:
            return "tactile"
        if "청축" in normalized:
            return "clicky"
        if noise_preference == "quiet":
            return "silent_linear_or_tactile"
        return "undecided"

    def _is_ambiguous_request(self, query: str, budget_max: int | None, noise_preference: str) -> bool:
        signals = [
            self._contains_any(query, KEYBOARD_TOKENS),
            self._contains_any(query, SWITCH_TOKENS),
            self._contains_any(query, LAYOUT_TOKENS),
            budget_max is not None,
            noise_preference != "undecided",
        ]
        return sum(signals) <= 1

    def _build_source_note(self, products: list[ProductPayload]) -> str:
        if not products:
            return "실시간 검색 결과와 내부 fallback 데이터를 함께 참고했습니다."
        live_count = sum(
            1 for product in products if self._candidate_source(product) == "serpapi_live"
        )
        mock_count = sum(
            1 for product in products if self._candidate_source(product).startswith("mock")
        )
        if live_count and mock_count:
            return "실시간 검색 결과를 우선 사용했고, 부족한 후보는 mock fallback 데이터로 보강했습니다."
        if live_count:
            return "실시간 검색 결과를 기준으로 후보를 정리했기 때문에 실제 재고와 가격은 다시 확인하는 편이 안전합니다."
        return "실시간 검색 결과가 부족해 mock fallback 데이터를 기준으로 후보를 정리했습니다."

    @staticmethod
    def _candidate_source(product: ProductPayload) -> str:
        if not isinstance(product.attributes, dict):
            return ""
        source = product.attributes.get("retrieval_source")
        return str(source) if source is not None else ""

    def _candidate_uses_mock_source(self, product: ProductPayload) -> bool:
        return self._candidate_source(product).startswith("mock")
