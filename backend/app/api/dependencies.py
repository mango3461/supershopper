from app.infra.container import AppContainer, get_container
from app.orchestrators.shopping_flow import ShoppingFlowOrchestrator
from app.services.response_formatter import ResponseFormatter


def get_app_container() -> AppContainer:
    return get_container()


def get_shopping_flow() -> ShoppingFlowOrchestrator:
    return get_container().shopping_flow


def get_response_formatter() -> ResponseFormatter:
    return get_container().response_formatter

