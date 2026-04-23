from fastapi import APIRouter, Depends

from app.api.dependencies import get_shopping_flow
from app.api.schemas.request import RecommendRequest
from app.api.schemas.response import RecommendResponse
from app.orchestrators.shopping_flow import ShoppingFlowOrchestrator


router = APIRouter()


@router.post("", response_model=RecommendResponse)
def recommend(
    request: RecommendRequest,
    flow: ShoppingFlowOrchestrator = Depends(get_shopping_flow),
) -> RecommendResponse:
    recommendation, workflow = flow.run_recommendation(request)
    return RecommendResponse(**recommendation.model_dump(), workflow=workflow)
