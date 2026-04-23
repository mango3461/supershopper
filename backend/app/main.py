from fastapi import FastAPI

from app.api.routes import chat, health, recommend
from app.infra.settings import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Initial FastAPI backend scaffold for the SuperShopper shopping assistant.",
)

app.include_router(health.router)
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(recommend.router, prefix="/recommend", tags=["recommend"])

