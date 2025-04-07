from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import os
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Check service health
    """
    health = {
        "status": "ok",
        "version": "1.0.0",
        "services": {
            "database": "ok",
            "recsys": "ok" 
        }
    }
    
    # Check database connection
    try:
        # Test DB connection
        await db.execute("SELECT 1")
    except Exception as e:
        health["services"]["database"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    # Check recommendation model
    model_path = settings.RECSYS_MODEL_PATH
    if not os.path.exists(model_path):
        health["services"]["recsys"] = "warning: model not found"
        if health["status"] == "ok":
            health["status"] = "warning"
    
    return health