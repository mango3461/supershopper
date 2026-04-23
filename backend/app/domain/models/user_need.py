from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserNeed:
    category: str
    user_level: str
    budget_min: float | None = None
    budget_max: float | None = None
    constraints: list[str] = field(default_factory=list)
    prioritized_attributes: list[str] = field(default_factory=list)

