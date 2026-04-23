from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewEvidence:
    source: str
    snippet: str
    rating: float | None = None
    url: str | None = None

