from app.domain.models.product_candidate import ProductCandidate


class PresentationPolicy:
    @staticmethod
    def next_actions(recommended_products: list[ProductCandidate]) -> list[str]:
        if not recommended_products:
            return ["Refine the budget or product constraints and rerun the workflow."]

        top_pick = recommended_products[0]
        return [
            f"Validate current pricing for {top_pick.name} before purchase.",
            "Compare warranty and return policy on the final shortlist.",
            "Review at least two recent user reviews for the top pick.",
        ]

