from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Dict

from app.api.dependencies import get_current_active_user, get_recsys_service
from app.db.session import get_db
from app.schemas.tweet import FeedTweet
from app.services.feed_generation import FeedGenerationService
from app.services.recsys import RecsysService

router = APIRouter()

@router.get("/", response_model=List[FeedTweet])
async def get_feed(
    count: int = Query(10, description="Number of tweets to return", ge=1, le=50),
    include_attention_checks: bool = Query(True, description="Whether to include attention checks"),
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    recsys: RecsysService = Depends(get_recsys_service),
) -> Any:
    """
    Get personalized feed for current user
    """
    feed_service = FeedGenerationService(db, recsys)
    return await feed_service.generate_feed(
        user_id=current_user["id"], 
        count=count,
        include_attention_checks=include_attention_checks
    )

@router.get("/trending", response_model=List[FeedTweet])
async def get_trending(
    count: int = Query(10, description="Number of trending tweets to return", ge=1, le=50),
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    recsys: RecsysService = Depends(get_recsys_service),
) -> Any:
    """
    Get trending tweets (most popular/viral)
    """
    feed_service = FeedGenerationService(db, recsys)
    # In a real app, this would return trending tweets
    # For now, returning the same as regular feed but without attention checks
    return await feed_service.generate_feed(
        user_id=current_user["id"], 
        count=count,
        include_attention_checks=False
    )