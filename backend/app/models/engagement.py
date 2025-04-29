from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Boolean
)

from app.db.base import Base


# class TwitterEngagements(Base):
#     __tablename__ = "engagements"
#     
#     tweet_id = Column(String, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("tweets.id"))
#     retweets = Column(Integer, default=0)
#     likes = Column(Integer, default=0)
#     comments = Column(Integer, default=0)
#     shares = Column(Integer, default=0)
#     liked = Column(Boolean, default=False)
#     retweeted = Column(Boolean, default=False)
#     liked_by = Column(String, default="")
#     retweeted_by = Column(String, default="")
#     tweet = relationship("Tweet")


class Engagement(Base):
    __tablename__ = "engagements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String, ForeignKey("social_posts.id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)
    
    engagement_type = Column(String, nullable=False)  # like, share, comment
    content = Column(String, nullable=True)  # For comments

    liked_by_user = Column(Boolean, default=False)
    shared_by_user = Column(Boolean, default=False)
    commens_by_yser = Column(Boolean, default=False)
