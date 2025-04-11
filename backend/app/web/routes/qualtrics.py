from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from typing import Any, Dict, Optional

from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/status")
async def get_qualtrics_status(
    survey_id: str = Query(..., description="Qualtrics survey ID"),
    current_user: Dict = Depends(get_current_active_user),
) -> Any:
    """
    Check if Qualtrics survey is active
    """
    # In a real app, this would check if a Qualtrics survey is active
    # For now, always return active
    return {
        "survey_id": survey_id,
        "status": "active",
        "user_eligible": True
    }

@router.post("/complete")
async def complete_survey(
    survey_data: Dict = Body(...),
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark survey as completed for user
    """
    # In a real app, this would validate the survey completion
    # and perhaps generate a completion code
    
    if "survey_id" not in survey_data:
        raise HTTPException(
            status_code=400,
            detail="survey_id is required"
        )
    
    # Generate completion code
    import random
    import string
    completion_code = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=10)
    )
    
    return {
        "success": True,
        "message": "Survey completion recorded",
        "completion_code": completion_code
    }

@router.get("/admin/responses", dependencies=[Depends(get_current_admin_user)])
async def get_survey_responses(
    survey_id: str = Query(..., description="Qualtrics survey ID"),
) -> Any:
    """
    Get survey responses (admin only)
    """
    # This would fetch responses from Qualtrics API
    if not settings.QUALTRICS_API_TOKEN:
        return {
            "error": "Qualtrics API not configured",
            "responses": []
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.QUALTRICS_BASE_URL}/surveys/{survey_id}/responses",
                headers={"X-API-TOKEN": settings.QUALTRICS_API_TOKEN}
            )
            return response.json()
    except Exception as e:
        return {
            "error": f"Failed to fetch responses: {str(e)}",
            "responses": []
        }