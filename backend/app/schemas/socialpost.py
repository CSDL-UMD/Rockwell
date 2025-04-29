from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class TweetBase(BaseModel):
    id: str
    author_id: str
    content: str
    blob: Dict
    created_at: datetime
    likes_count: int = 0
    retweets_count: int = 0
    replies_count: int = 0
    media_urls: Optional[List[str]] = None
    tweet_metadata: Optional[Dict[str, Any]] = None

class TweetCreate(TweetBase):
    pass

class TweetUpdate(TweetBase):
    pass

class Tweet(TweetBase):
    class Config:
        from_attributes = True

class FeedTweet(Tweet):
    ranking_score: Optional[float] = None
    is_attention_check: bool = False
