from typing import Optional
from pydantic import BaseModel, Field, NonNegativeInt  

class TwitterEngagements(BaseModel):
    """Engagement counts from Twitter"""

    retweets: NonNegativeInt = 0
    likes: NonNegativeInt = 0
    comments: NonNegativeInt = 0
    shares: NonNegativeInt = 0  

    liked: bool = Field(default=False, description="Whether the user has liked this tweet")
    retweeted: bool = Field(default=False, description="Whether the user has retweeted this tweet")
    
    retweet_by: Optional[str] = None
    quoted_by: Optional[str] = None