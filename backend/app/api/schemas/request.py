from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    constraints: list[str] = Field(default_factory=list)
    max_candidates: int = Field(default=3, ge=1, le=5)


class RecommendRequest(BaseModel):
    query: str = Field(min_length=1)
    budget_min: float | None = None
    budget_max: float | None = None
    constraints: list[str] = Field(default_factory=list)
    max_candidates: int = Field(default=3, ge=1, le=5)

