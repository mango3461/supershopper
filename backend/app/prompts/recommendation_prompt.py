from app.api.schemas.common import IntentAnalysisPayload, ProductPayload, SummaryPayload


RECOMMENDATION_PROMPT = """Generate a recommendation from ranked candidates.
Category: {category}
Summary: {summary}
Candidates: {candidate_names}
Return:
- recommendation_reason
- caution_or_uncertainty
"""


def render(
    intent: IntentAnalysisPayload, summary: SummaryPayload, ranked_candidates: list[ProductPayload]
) -> str:
    candidate_names = ", ".join(product.name for product in ranked_candidates[:3]) or "none"
    return RECOMMENDATION_PROMPT.format(
        category=intent.category,
        summary=summary.summary,
        candidate_names=candidate_names,
    )
