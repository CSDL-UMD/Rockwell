from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Body, Query, Path, Request
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List

from app.api.dependencies import get_current_active_user, get_recsys_service
from app.db.session import get_db, get_store
from app.models.engagement import EngagementType
from app.schemas.engagement import Engagement, EngagementCreate
from app.services.recsys import RecsysService
from app.db.repositories.tweet import TweetRepository

router = APIRouter()

@router.post("/", response_model=Engagement)
async def create_engagement(
    request: Request,
    background_tasks: BackgroundTasks,
    engagement_in: EngagementCreate = Body(...),
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    recsys: RecsysService = Depends(get_recsys_service),
) -> Any:
    """
    Record user engagement with a tweet
    """
    worker_id = request.headers.get("worker_id")
    experimental_condition = get_store("experimental_condition")

    print("WORKER ID IN GET FEED!!!")
    print(worker_id)

    experimental_condition_val = ""
    if worker_id in experimental_condition.keys():
        experimental_condition_val = experimental_condition[worker_id]

    feedtype = 'L' if experimental_condition_val == 'treatment' else 'M'
    attn = int(request.args.get('attn'))
    page = int(request.args.get('page'))

    session_id = -1
    if attn == 0 and page == 0:
        insert_session_payload = {'worker_id': worker_id}
        resp_session_id = requests.get('http://127.0.0.1:5052/insert_session',params=insert_session_payload)
        session_id = resp_session_id.json()["data"]
        session_id_store[worker_id] = session_id
        #db_response_attn = requests.get('http://127.0.0.1:5052/get_existing_attn_tweets_new?worker_id='+str(worker_id)+"&page=NA&feedtype="+feedtype)
        #db_response_attn = db_response_attn.json()['data']
        db_response_timeline = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page=NA&feedtype="+feedtype)
        db_response_timeline = db_response_timeline.json()['data']
        attn_payload = []
        attn_pages = []
        #for attn_tweet in db_response_attn:
        #    db_tweet = {
        #        'tweet_id': attn_tweet[0],
        #        'page' : attn_tweet[2],
        #        'rank' : attn_tweet[3],
        #        'present' : attn_tweet[1]
        #    }
        #    attn_payload.append(db_tweet)
        #    attn_pages.append(int(attn_tweet[2]))
        #max_page_store[worker_id] = max(attn_pages)
        max_page_store[worker_id] = 1
        timeline_payload = []
        for timeline_tweet in db_response_timeline:
            db_tweet = {
                'fav_before': timeline_tweet[2],
                'tid' : timeline_tweet[0],
                'rtbefore' : timeline_tweet[3],
                'page' : timeline_tweet[4],
                'rank' : timeline_tweet[5],
                'predicted_score' : timeline_tweet[6]
            }
            timeline_payload.append(db_tweet)
        finalJson = []
        finalJson.append(session_id)
        finalJson.append(feedtype)
        finalJson.append(timeline_payload)
        finalJson.append(attn_payload)
        requests.post('http://127.0.0.1:5052/insert_timelines_attention_in_session',json=finalJson)
        db_response_timeline_screen_2 = requests.get('http://127.0.0.1:5052/get_existing_tweets_new_screen_2?worker_id='+str(worker_id)+"&page=NA&feedtype="+feedtype)
        db_response_timeline_screen_2 = db_response_timeline_screen_2.json()['data']
        timeline_payload = []
        for timeline_tweet in db_response_timeline_screen_2:
            db_tweet = {
                'tid' : timeline_tweet[0],
                'page' : timeline_tweet[4],
                'rank' : timeline_tweet[5],
                'predicted_score' : timeline_tweet[6]
            }
            timeline_payload.append(db_tweet)
        finalJson = []
        finalJson.append(session_id)
        finalJson.append(feedtype)
        finalJson.append(timeline_payload)
        requests.post('http://127.0.0.1:5052/insert_timelines_attention_in_session_screen_2',json=finalJson)
    else:
        session_id_store = get_store("session_id_store")
        session_id = session_id_store[worker_id]
    if attn == 1:
        print("Here!!")
        print(worker_id)
        print(page)
        db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new_screen_2?worker_id='+str(worker_id)+"&page="+str(page)+"&feedtype="+feedtype)
        db_response = db_response.json()['data']
        if db_response == "NEW":
            feed_json = []
            feed_json.append({"anything_present":"NO"})
            return jsonify(feed_json)
        public_tweets = [d[4] for d in db_response]
        public_tweets_v2 = [d[4] for d in db_response]
        domains = [d[6] for d in db_response]
        if len(db_response[0]) > 5:
            public_tweets_v2 = [d[5] for d in db_response]    
    else:
        print("page:::")
        print(page)
        print(worker_id)   
        db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page="+str(page)+"&feedtype="+feedtype)
        db_response = db_response.json()['data']
        if db_response == "NEW":
            feed_json = []
            feed_json.append({"anything_present":"NO"})
            return feed_json
        public_tweets = [d[4] for d in db_response]
        public_tweets_v2 = [d[4] for d in db_response]
        domains = [d[6] for d in db_response]
        if len(db_response[0]) > 5:
            public_tweets_v2 = [d[5] for d in db_response]







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

@router.get("retweeet/{tweet_id}", response_model=List[Engagement])
async def retweet(
    tweet_id: str = Path(..., description="ID of the tweet to retweet"),
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get retweet engagements for a specific tweet
    """
    from sqlalchemy import select
    from app.models.engagement import Engagement, EngagementType
    
    # Build query
    query = select(Engagement).where(
        Engagement.tweet_id == tweet_id,
        Engagement.user_id == current_user["id"],
        Engagement.engagement_type == EngagementType.RETWEET
    )
    
    # Execute query
    result = await db.execute(query)
    retweets = result.scalars().all()
    return retweets


