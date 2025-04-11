from fastapi import APIRouter
from app.web.routes import auth, qualtrics

web_router = APIRouter()

web_router.include_router(auth.router, prefix="/auth", tags=["auth"])
web_router.include_router(qualtrics.router, prefix="/qualtrics", tags=["qualtrics"])