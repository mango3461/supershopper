from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchStrategy:
    queries: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    max_products: int = 5

