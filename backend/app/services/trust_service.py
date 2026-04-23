from app.api.schemas.common import ProductPayload, ReviewSnippet
from app.domain.models.product_candidate import ProductCandidate
from app.domain.models.review_evidence import ReviewEvidence
from app.domain.policies.confidence_policy import ConfidencePolicy


class TrustService:
    def apply(self, products: list[ProductPayload]) -> list[ProductPayload]:
        scored_products: list[ProductPayload] = []
        for product in products:
            candidate = ProductCandidate(
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
            trust_score = ConfidencePolicy.score(candidate)
            scored_products.append(product.model_copy(update={"trust_score": trust_score}))
        return scored_products

