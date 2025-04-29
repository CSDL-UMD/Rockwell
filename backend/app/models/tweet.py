# from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, ForeignKey
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from app.db.base import Base
#
#
# class Tweet(Base):
#     __tablename__ = "tweets"
#
#     id = Column(String, primary_key=True, index=True)
#     body = Column(String, nullable=False)
#     actor_username = Column(String, default="")
#     actor_picture = Column(String, default="")
#     domain_present = Column(String, default="")
#     type = Column(String, default="")
#     created_at = Column(DateTime(timezone=True), nullable=False)
#     likes_count = Column(Integer, default=0)
#     retweets_count = Column(Integer, default=0)
#     replies_count = Column(Integer, default=0)
#     embeded_images = Column(JSON, nullable=True)
#     embeded_images = Column(JSON, nullable=True)
#     tweet_metadata = Column(JSON, nullable=True)
#     imported_at = Column(DateTime(timezone=True), server_default=func.now())
#     language = Column(String, default="en")
#     engagements = relationship("TwitterEngagements")
