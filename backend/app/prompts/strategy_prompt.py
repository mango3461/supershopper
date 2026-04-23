from app.api.schemas.common import IntentAnalysisPayload


STRATEGY_PROMPT = """Create 3-5 shopping search queries for mechanical keyboard retrieval.
Category: {category}
User level: {user_level}
Budget max: {budget_max}
Constraints: {constraints}
Return query text plus rationale for each query.
"""


def render(intent: IntentAnalysisPayload) -> str:
    return STRATEGY_PROMPT.format(
        category=intent.category,
        user_level=intent.user_level,
        budget_max=intent.budget.max_price,
        constraints=", ".join(intent.constraints) or "none",
    )
