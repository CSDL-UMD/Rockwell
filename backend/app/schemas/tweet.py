from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class TweetBase(BaseModel):
    id: str
    author_id: str
    content: str
    created_at: datetime
    likes_count: int = 0
    retweets_count: int = 0
    replies_count: int = 0
    media_urls: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class TweetCreate(TweetBase):
    pass

class Tweet(TweetBase):
    class Config:
        from_attributes = True

class FeedTweet(Tweet):
    ranking_score: Optional[float] = None
    is_attention_check: bool = False