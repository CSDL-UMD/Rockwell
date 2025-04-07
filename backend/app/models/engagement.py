from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from app.db.base import Base

class EngagementType(enum.Enum):
    LIKE = "like"
    RETWEET = "retweet"
    REPLY = "reply"
    VIEW = "view"
    CLICK = "click"
    ATTENTION_CHECK = "attention_check"

class Engagement(Base):
    __tablename__ = "engagements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tweet_id = Column(String, ForeignKey("tweets.id"), nullable=False)
    engagement_type = Column(Enum(EngagementType), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Time spent viewing before engagement
    response_correct = Column(Boolean, nullable=True)  # For attention checks
    metadata = Column(String, nullable=True)  # Any additional info as JSON string