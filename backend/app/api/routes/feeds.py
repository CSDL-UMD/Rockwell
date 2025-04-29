import datetime
from fastapi import APIRouter, Depends, Query, Request
import requests
from typing import List, Any, Dict

from app.api.dependencies import get_current_user, get_recsys_service, get_db
from app.db.session import get_store
from app.schemas.post import FeedItem, FeedResponse 
from app.services.feed_generation import FeedGenerationService
from app.services.recsys import RecsysService
from app.services.post import PostService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/get_feed", response_model=FeedResponse)
async def get_feed(
    request: Request,
    count: int = Query(10, description="Number of tweets to return", ge=1, le=50),
    include_attention_checks: bool = Query(False, description="Whether to include attention checks"),
    current_user: Dict = Depends(get_current_user),
    recsys: RecsysService = Depends(get_recsys_service),
) -> Any:
    """
    Get personalized feed for current user
    """

    feed_service = FeedGenerationService(recsys)

    worker_id = request.headers.get("worker_id")
    experimental_condition = get_store("experimental_condition")

    time_now = datetime.datetime.now()
    worker_id = str(request.args.get('worker_id')).strip()

    print("WORKER ID IN GET FEED!!!")
    print(worker_id)

    experimental_condition_val = ""
    if worker_id in experimental_condition.keys():
        experimental_condition_val = experimental_condition[worker_id]

    experimental_condition_val =  "L" if experimental_condition_val == 'treatment' else "M"

    attn = int(request.args.get('attn'))
    page = int(request.args.get('page'))
    session_id = -1
    
    return await feed_service.generate_feed(
        user_id=current_user["id"], 
        count=count,
        include_attention_checks=include_attention_checks
    )

# @router.get("/feed", response_model=FeedResponse)
@router.get("/feed")
async def feed(
    request: Request,
    count: int = Query(2, description="Number of tweets to return", ge=1, le=50),
    include_attention_checks: bool = Query(False, description="Whether to include attention checks"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get personalized feed for current user
    """
    posts = PostService(db) 
    feed_service = FeedGenerationService(None, posts)

    feeds = await feed_service.generate_feed(None, 10, False)

    
    return {"items":feeds}
