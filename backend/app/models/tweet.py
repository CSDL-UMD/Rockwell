from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(String, primary_key=True, index=True)
    author_id = Column(String, index=True, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    likes_count = Column(Integer, default=0)
    retweets_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    media_urls = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())