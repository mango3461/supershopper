from pydantic import BaseModel, Field

from app.api.schemas.common import (
    RecommendationDebugPayload,
    IntentAnalysisPayload,
    ProductPayload,
    RecommendationPayload,
    SearchQuery,
    SummaryPayload,
    WorkflowTrace,
)


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    llm_mode: str
    search_mode: str
    cache_mode: str
    workflow_order: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    recommendation: RecommendationPayload
    workflow: WorkflowTrace


class RecommendResponse(BaseModel):
    interpreted_intent: IntentAnalysisPayload
    generated_search_queries: list[SearchQuery] = Field(default_factory=list)
    buying_guide_summary: SummaryPayload
    top_candidates: list[ProductPayload] = Field(default_factory=list)
    recommended_choice: ProductPayload | None = None
    recommendation_reason: str
    caution_or_uncertainty: list[str] = Field(default_factory=list)
    debug: RecommendationDebugPayload | None = None
    workflow: WorkflowTrace
