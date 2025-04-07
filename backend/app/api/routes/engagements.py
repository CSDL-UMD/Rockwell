from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Body, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List

from app.api.dependencies import get_current_active_user, get_recsys_service
from app.db.session import get_db
from app.models.engagement import EngagementType
from app.schemas.engagement import Engagement, EngagementCreate
from app.services.recsys import RecsysService
from app.db.repositories.tweet import TweetRepository

router = APIRouter()

@router.post("/", response_model=Engagement)
async def create_engagement(
    background_tasks: BackgroundTasks,
    engagement_in: EngagementCreate = Body(...),
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    recsys: RecsysService = Depends(get_recsys_service),
) -> Any:
    """
    Record user engagement with a tweet
    """
    # Verify the user ID in the request matches the authenticated user
    if engagement_in.user_id != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="User ID in request doesn't match authenticated user",
        )
    
    # Verify the tweet exists
    tweet_repo = TweetRepository(db)
    tweet = await tweet_repo.get(id=engagement_in.tweet_id)
    if not tweet:
        raise HTTPException(
            status_code=404,
            detail="Tweet not found",
        )
    
    # Create the engagement record
    from app.db.repositories.base import BaseRepository
    from app.models.engagement import Engagement as EngagementModel
    
    engagement_repo = BaseRepository[EngagementModel, EngagementCreate, EngagementCreate](
        EngagementModel, db
    )
    engagement = await engagement_repo.create(obj_in=engagement_in)
    
    # Update recommendation system in background
    background_tasks.add_task(
        recsys.record_engagement,
        current_user["id"],
        engagement_in.tweet_id,
        engagement_in.engagement_type.value
    )
    
    return engagement

@router.get("/attention-checks", response_model=List[Engagement])
async def get_attention_checks(
    session_id: str = Query(None, description="Filter by session ID"),
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get attention check engagements for current user
    """
    from sqlalchemy import select
    from app.models.engagement import Engagement, EngagementType
    
    # Build query
    query = select(Engagement).where(
        Engagement.user_id == current_user["id"],
        Engagement.engagement_type == EngagementType.ATTENTION_CHECK
    )
    
    # Add session filter if provided
    if session_id:
        query = query.where(Engagement.session_id == session_id)
    
    # Execute query
    result = await db.execute(query)
    attention_checks = result.scalars().all()
    return attention_checks