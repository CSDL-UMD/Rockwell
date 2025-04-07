from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.engagement import EngagementType

class EngagementBase(BaseModel):
    user_id: str
    tweet_id: str
    engagement_type: EngagementType
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None
    response_correct: Optional[bool] = None
    metadata: Optional[str] = None

class EngagementCreate(EngagementBase):
    pass

class Engagement(EngagementBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True