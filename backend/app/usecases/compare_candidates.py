from app.api.schemas.common import ProductPayload, ReviewSnippet
from app.domain.models.product_candidate import ProductCandidate
from app.domain.models.review_evidence import ReviewEvidence
from app.domain.policies.ranking_policy import RankingPolicy
from app.ports.logger_port import LoggerPort


class CompareCandidatesUseCase:
    def __init__(self, logger: LoggerPort) -> None:
        self._logger = logger

    def execute(self, products: list[ProductPayload]) -> list[ProductPayload]:
        ranked_domain_products = RankingPolicy.rank(
            [
                ProductCandidate(
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
                    relevance_score=product.relevance_score,
                    trust_score=product.trust_score,
                    match_score=product.match_score,
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
                for product in products
            ]
        )
        ranked_products = [
            ProductPayload(
                product_id=item.product_id,
                name=item.name,
                brand=item.brand,
                price=item.price,
                currency=item.currency,
                url=item.url,
                layout=item.layout,
                switch_type=item.switch_type,
                noise_level=item.noise_level,
                key_feel=item.key_feel,
                attributes=item.attributes,
                relevance_score=item.relevance_score,
                trust_score=item.trust_score,
                match_score=item.match_score,
                evidence=[
                    ReviewSnippet(
                        source=evidence.source,
                        snippet=evidence.snippet,
                        rating=evidence.rating,
                        url=evidence.url,
                    )
                    for evidence in item.evidence
                ],
            ).model_copy(
                update={
                    "connectivity": next(
                        product.connectivity
                        for product in products
                        if product.product_id == item.product_id
                    ),
                    "hot_swappable": next(
                        product.hot_swappable
                        for product in products
                        if product.product_id == item.product_id
                    ),
                    "beginner_friendly": next(
                        product.beginner_friendly
                        for product in products
                        if product.product_id == item.product_id
                    ),
                    "strengths": next(
                        product.strengths for product in products if product.product_id == item.product_id
                    ),
                    "cautions": next(
                        product.cautions for product in products if product.product_id == item.product_id
                    ),
                    "why_it_matches": next(
                        product.why_it_matches
                        for product in products
                        if product.product_id == item.product_id
                    ),
                    "evidence_summary": next(
                        product.evidence_summary
                        for product in products
                        if product.product_id == item.product_id
                    ),
                }
            )
            for item in ranked_domain_products
        ]
        self._logger.debug(f"Ranked {len(ranked_products)} product candidates")
        return ranked_products
