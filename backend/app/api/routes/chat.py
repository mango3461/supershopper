from fastapi import APIRouter, Depends

from app.api.dependencies import get_response_formatter, get_shopping_flow
from app.api.schemas.request import ChatRequest
from app.api.schemas.response import ChatResponse
from app.orchestrators.shopping_flow import ShoppingFlowOrchestrator
from app.services.response_formatter import ResponseFormatter


router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    flow: ShoppingFlowOrchestrator = Depends(get_shopping_flow),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> ChatResponse:
    recommendation, workflow = flow.run_chat(request)
    reply = formatter.format_chat_reply(recommendation)
    return ChatResponse(reply=reply, recommendation=recommendation, workflow=workflow)

