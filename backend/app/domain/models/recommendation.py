from dataclasses import dataclass, field

from app.domain.models.product_candidate import ProductCandidate


@dataclass(frozen=True)
class Recommendation:
    recommended_products: list[ProductCandidate] = field(default_factory=list)
    rationale: str = ""
    next_actions: list[str] = field(default_factory=list)
    summary: str = ""

