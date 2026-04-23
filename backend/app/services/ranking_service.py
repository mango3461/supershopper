from app.api.schemas.common import ProductPayload, ReviewSnippet
from app.domain.models.product_candidate import ProductCandidate
from app.domain.models.review_evidence import ReviewEvidence
from app.domain.policies.ranking_policy import RankingPolicy


class RankingService:
    def rank(self, products: list[ProductPayload]) -> list[ProductPayload]:
        domain_candidates = [
            ProductCandidate(
                product_id=product.product_id,
                name=product.name,
                brand=product.brand,
                price=product.price,
                currency=product.currency,
                url=product.url,
                attributes=product.attributes,
                relevance_score=product.relevance_score,
                trust_score=product.trust_score,
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

        ranked = RankingPolicy.rank(domain_candidates)
        return [
            ProductPayload(
                product_id=item.product_id,
                name=item.name,
                brand=item.brand,
                price=item.price,
                currency=item.currency,
                url=item.url,
                attributes=item.attributes,
                relevance_score=item.relevance_score,
                trust_score=item.trust_score,
                evidence=[
                    ReviewSnippet(
                        source=evidence.source,
                        snippet=evidence.snippet,
                        rating=evidence.rating,
                        url=evidence.url,
                    )
                    for evidence in item.evidence
                ],
            )
            for item in ranked
        ]

