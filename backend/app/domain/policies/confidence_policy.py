from app.domain.models.product_candidate import ProductCandidate


class ConfidencePolicy:
    @staticmethod
    def score(candidate: ProductCandidate) -> float:
        if not candidate.evidence:
            return 0.2

        ratings = [e.rating for e in candidate.evidence if e.rating is not None]
        average_rating = sum(ratings) / len(ratings) if ratings else 4.0
        evidence_factor = min(len(candidate.evidence) / 3, 1.0)
        rating_factor = min(max(average_rating / 5, 0.0), 1.0)
        return round((evidence_factor * 0.6) + (rating_factor * 0.4), 3)

