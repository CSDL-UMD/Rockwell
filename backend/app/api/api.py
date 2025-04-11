from fastapi import APIRouter
from app.api.routes import feeds, engagements, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
api_router.include_router(engagements.router, prefix="/engagements", tags=["engagements"])