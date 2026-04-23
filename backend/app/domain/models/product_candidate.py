from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models.review_evidence import ReviewEvidence


@dataclass(frozen=True)
class ProductCandidate:
    product_id: str
    name: str
    brand: str | None = None
    price: float | None = None
    currency: str = "KRW"
    url: str | None = None
    layout: str | None = None
    switch_type: str | None = None
    noise_level: str | None = None
    key_feel: str | None = None
    attributes: dict[str, object] = field(default_factory=dict)
    relevance_score: float = 0.0
    trust_score: float = 0.0
    match_score: float = 0.0
    evidence: list[ReviewEvidence] = field(default_factory=list)
