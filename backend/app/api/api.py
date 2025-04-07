from fastapi import APIRouter
from app.api.routes import auth, feeds, engagements, qualtrics, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
api_router.include_router(engagements.router, prefix="/engagements", tags=["engagements"])
api_router.include_router(qualtrics.router, prefix="/qualtrics", tags=["qualtrics"])