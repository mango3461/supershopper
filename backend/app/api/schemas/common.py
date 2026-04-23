from typing import Any, Literal

from pydantic import BaseModel, Field


ProviderMode = Literal["mock", "configured"]
WorkflowStatus = Literal["pending", "completed", "failed"]
UserLevel = Literal["beginner", "intermediate", "advanced"]


class UserQueryPayload(BaseModel):
    query: str = Field(min_length=1)
    budget_min: float | None = None
    budget_max: float | None = None
    constraints: list[str] = Field(default_factory=list)
    max_candidates: int = Field(default=3, ge=1, le=5)
    session_id: str | None = None


class SearchQuery(BaseModel):
    query: str
    rationale: str


class ReviewSnippet(BaseModel):
    source: str
    snippet: str
    rating: float | None = None
    url: str | None = None


class BudgetPayload(BaseModel):
    currency: str = "KRW"
    min_price: int | None = None
    max_price: int | None = None


class ProductPayload(BaseModel):
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
    connectivity: list[str] = Field(default_factory=list)
    hot_swappable: bool | None = None
    beginner_friendly: bool = True
    strengths: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    why_it_matches: list[str] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence: list[ReviewSnippet] = Field(default_factory=list)
    relevance_score: float = 0.0
    trust_score: float = 0.0
    match_score: float = 0.0


class IntentAnalysisPayload(BaseModel):
    original_query: str
    category: str = "mechanical_keyboard"
    category_label: str = "Mechanical Keyboard"
    user_level: UserLevel = "beginner"
    use_case: str = "First mechanical keyboard purchase"
    budget: BudgetPayload = Field(default_factory=BudgetPayload)
    constraints: list[str] = Field(default_factory=list)
    prioritized_attributes: list[str] = Field(default_factory=list)
    preferred_noise_level: str = "quiet"
    preferred_key_feel: str = "silent_linear_or_tactile"
    preferred_layout: str = "undecided"
    desired_features: list[str] = Field(default_factory=list)
    comparison_axes: list[str] = Field(default_factory=list)
    interpretation_summary: str = ""
    confidence_score: float = 0.0


class SearchStrategyPayload(BaseModel):
    queries: list[SearchQuery] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=lambda: ["shopping", "reviews"])
    max_products: int = Field(default=5, ge=1, le=10)
    strategy_note: str = ""


class ExpertSignalPayload(BaseModel):
    signal_id: str
    title: str
    source: str
    snippet: str = ""
    url: str | None = None
    signal_type: str = "guide"
    mentioned_products: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    retrieval_source: str = ""
    fallback_reason: str | None = None


class CandidateSeedPayload(BaseModel):
    candidate_id: str
    name: str
    brand: str | None = None
    category: str = "mechanical_keyboard"
    reference_price: float | None = None
    inferred_layout: str | None = None
    inferred_switch_type: str | None = None
    inferred_noise_level: str | None = None
    beginner_friendly: bool = True
    rationale_signals: list[str] = Field(default_factory=list)
    source_signal_titles: list[str] = Field(default_factory=list)
    source_signal_mode: str = "unknown"
    generation_reason: str = ""
    candidate_source_reason: str = ""
    heuristic_score: float = 0.0


class ExpertSignalsPayload(BaseModel):
    strategy: SearchStrategyPayload
    signals: list[ExpertSignalPayload] = Field(default_factory=list)


class CandidateGenerationPayload(BaseModel):
    strategy: SearchStrategyPayload
    expert_signals: list[ExpertSignalPayload] = Field(default_factory=list)
    candidates: list[CandidateSeedPayload] = Field(default_factory=list)


class RetrievalPayload(BaseModel):
    strategy: SearchStrategyPayload
    products: list[ProductPayload] = Field(default_factory=list)


class EvidenceFilteringPayload(BaseModel):
    strategy: SearchStrategyPayload
    products: list[ProductPayload] = Field(default_factory=list)
    dropped_reasons: dict[str, str] = Field(default_factory=dict)


class SummaryPayload(BaseModel):
    summary: str
    comparison_points: list[str] = Field(default_factory=list)
    beginner_tip: str
    tradeoff_note: str


class RecommendationWordingPayload(BaseModel):
    recommendation_reason: str
    caution_or_uncertainty: list[str] = Field(default_factory=list)


class RecommendationDebugPayload(BaseModel):
    expert_signal_source_mode: str = "unknown"
    expert_signals: list[ExpertSignalPayload] = Field(default_factory=list)
    generated_candidates: list[CandidateSeedPayload] = Field(default_factory=list)


class RecommendationPayload(BaseModel):
    interpreted_intent: IntentAnalysisPayload
    generated_search_queries: list[SearchQuery] = Field(default_factory=list)
    buying_guide_summary: SummaryPayload
    top_candidates: list[ProductPayload] = Field(default_factory=list)
    recommended_choice: ProductPayload | None = None
    recommendation_reason: str
    caution_or_uncertainty: list[str] = Field(default_factory=list)
    debug: RecommendationDebugPayload | None = None


class ProviderStatusPayload(BaseModel):
    llm: ProviderMode
    search: ProviderMode
    cache: ProviderMode


class WorkflowStepStatus(BaseModel):
    step: str
    status: WorkflowStatus = "completed"
    detail: str | None = None


class WorkflowTrace(BaseModel):
    workflow_order: list[str] = Field(default_factory=list)
    steps: list[WorkflowStepStatus] = Field(default_factory=list)
    providers: ProviderStatusPayload
