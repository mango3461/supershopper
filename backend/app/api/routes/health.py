from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_container
from app.api.schemas.response import HealthResponse
from app.domain.constants import WORKFLOW_ORDER
from app.infra.container import AppContainer
from app.infra.settings import get_settings


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(container: AppContainer = Depends(get_app_container)) -> HealthResponse:
    settings = get_settings()
    provider_status = container.provider_status()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
        llm_mode=provider_status.llm,
        search_mode=provider_status.search,
        cache_mode=provider_status.cache,
        workflow_order=list(WORKFLOW_ORDER),
    )

