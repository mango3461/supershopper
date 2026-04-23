from app.domain.models.product_candidate import ProductCandidate


class RankingPolicy:
    @staticmethod
    def rank(candidates: list[ProductCandidate]) -> list[ProductCandidate]:
        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.match_score,
                candidate.trust_score,
                -(candidate.price or 0.0),
            ),
            reverse=True,
        )
