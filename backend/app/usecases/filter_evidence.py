from app.api.schemas.common import EvidenceFilteringPayload, IntentAnalysisPayload, RetrievalPayload
from app.domain.models.product_candidate import ProductCandidate
from app.domain.models.review_evidence import ReviewEvidence
from app.domain.policies.confidence_policy import ConfidencePolicy
from app.ports.logger_port import LoggerPort


class FilterEvidenceUseCase:
    def __init__(self, logger: LoggerPort) -> None:
        self._logger = logger

    def execute(
        self, intent: IntentAnalysisPayload, retrieval: RetrievalPayload
    ) -> EvidenceFilteringPayload:
        dropped_reasons: dict[str, str] = {}
        filtered_products = []
        budget_max = intent.budget.max_price
        quiet_required = intent.preferred_noise_level == "quiet"

        for product in retrieval.products:
            if budget_max is not None and product.price is not None and product.price > budget_max:
                dropped_reasons[product.product_id] = "설정한 예산을 초과해 제외했습니다."
                continue

            if quiet_required and product.noise_level == "loud":
                dropped_reasons[product.product_id] = "스위치 소음이 큰 편이라 제외했습니다."
                continue

            domain_candidate = ProductCandidate(
                product_id=product.product_id,
                name=product.name,
                brand=product.brand,
                price=product.price,
                currency=product.currency,
                url=product.url,
                layout=product.layout,
                switch_type=product.switch_type,
                noise_level=product.noise_level,
                key_feel=product.key_feel,
                attributes=product.attributes,
                evidence=[
                    ReviewEvidence(
                        source=evidence.source,
                        snippet=evidence.snippet,
                        rating=evidence.rating,
                        url=evidence.url,
                    )
                    for evidence in product.evidence
                ],
            )
            trust_score = ConfidencePolicy.score(domain_candidate)
            match_score, why_it_matches, cautions = self._score_product(intent, product)

            filtered_products.append(
                product.model_copy(
                    update={
                        "trust_score": trust_score,
                        "match_score": match_score,
                        "relevance_score": match_score,
                        "why_it_matches": why_it_matches,
                        "cautions": cautions,
                        "evidence_summary": [item.snippet for item in product.evidence[:2]],
                    }
                )
            )

        self._logger.debug(
            f"Filtered evidence to {len(filtered_products)} candidates from {len(retrieval.products)}"
        )
        return EvidenceFilteringPayload(
            strategy=retrieval.strategy,
            products=filtered_products,
            dropped_reasons=dropped_reasons,
        )

    @staticmethod
    def _score_product(
        intent: IntentAnalysisPayload, product
    ) -> tuple[float, list[str], list[str]]:
        score = 0.0
        reasons: list[str] = []
        cautions = list(product.cautions)

        if intent.budget.max_price is not None and product.price is not None:
            if product.price <= intent.budget.max_price:
                score += 0.30
                reasons.append("설정한 예산 범위 안에 듭니다.")
            elif product.price <= int(intent.budget.max_price * 1.05):
                score += 0.08
                cautions.append("예산 상한선에 가깝습니다.")

        if intent.preferred_noise_level == "quiet":
            if product.noise_level == "quiet":
                score += 0.30
                reasons.append("조용한 스위치 성향이라 공유 공간에서도 무난합니다.")
            elif product.noise_level == "moderate":
                score += 0.10
                cautions.append("원하는 소음 수준보다는 약간 크게 느껴질 수 있습니다.")

        if product.beginner_friendly:
            score += 0.20
            reasons.append("처음 사는 사람도 무난하게 쓰기 좋습니다.")

        if intent.preferred_key_feel == "silent_linear_or_tactile":
            if product.switch_type in {"silent_linear", "silent_tactile"}:
                score += 0.12
                reasons.append("입문자에게 무난한 저소음 스위치 계열입니다.")
        elif intent.preferred_key_feel == product.switch_type:
            score += 0.12
            reasons.append("원하는 스위치 키감과 맞습니다.")

        if intent.preferred_layout == "undecided":
            if product.layout in {"75%", "TKL"}:
                score += 0.06
                reasons.append("핵심 키를 유지하면서도 책상 점유를 줄이는 배열입니다.")
        elif intent.preferred_layout == product.layout:
            score += 0.08
            reasons.append("원하는 배열 선호와 맞습니다.")

        if product.hot_swappable:
            score += 0.02
            reasons.append("핫스왑 지원으로 나중에 스위치를 바꾸기 쉬운 편입니다.")

        return round(score, 3), reasons, cautions
