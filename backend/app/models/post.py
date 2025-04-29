import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.interaction import InteractionType


class PlatformType(enum.Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"

class ContentType(enum.Enum):
    ORIGINAL = "original"      # Original content
    RESHARE = "reshare"        # Simple reshare/retweet
    QUOTE = "quote"            # Quote tweet/share with comment
    REPLY = "reply"            # Reply to another post


# Post model (unified for platform posts and internal posts)
class Post(Base):
    __tablename__ = "posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Source information
    platform = Column(Enum(PlatformType), nullable=False, index=True)
    external_id = Column(String, nullable=True, index=True)  # NULL for internal posts
    
    # Author information
    author_id = Column(String, ForeignKey("users.id"), nullable=True)  # Can be NULL for external posts
    external_author_id = Column(String, nullable=True)  # For platform posts
    external_author_name = Column(String, nullable=True)
    external_author_username = Column(String, nullable=True)
    
    # Content
    content = Column(Text, nullable=True)
    media_urls = Column(JSON, nullable=True)  # Array of media URLs


    # is_reply = Column(Boolean, default=False)
    # is_quote = Column(Boolean, default=False)
    # is_reshare = Column(Boolean, default=False)

    # likes_count = Column(Integer, default=0)
    # reshares_count = Column(Integer, default=0)
    # comments_count = Column(Integer, default=0)    

    # Post metadata
    content_type = Column(Enum(ContentType), default=ContentType.ORIGINAL, nullable=False)
    reference_post_id = Column(String, ForeignKey("posts.id"), nullable=True)  # For reshares, quotes, replies
    
    # Timestamps
    # created_at = Column(Date, nullable=False)
    created_at:  Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow         # DB will fill this if you omit it
    )
    # updated_at = Column(DateTime(), onupdate=func.now())

    # created_at = Column(String, nullable=False, server_default=func.now())
    # updated_at = Column(String, onupdate=func.now())
    
    # Platform-specific data
    # platform_data = Column(JSON, nullable=True)
    platform_metrics = Column(JSON, nullable=True)  # Likes, shares, etc. from the platform
    
    # Relationships
    author = relationship("User", back_populates="posts")
    referenced_post = relationship("Post", remote_side=[id], backref="referencing_posts")
    interactions = relationship("Interaction", back_populates="post")
    
    # Convenience methods for interaction counts
    @property
    def likes_count(self):
        return sum(1 for i in self.interactions if i.interaction_type == InteractionType.LIKE)
    
    @property
    def comments_count(self):
        return sum(1 for i in self.interactions if i.interaction_type == InteractionType.COMMENT)
    
    @property
    def reshares_count(self):
        return sum(1 for i in self.interactions 
                  if i.interaction_type in [InteractionType.RESHARE, InteractionType.QUOTE])
    
    @property
    def total_likes_count(self):
        platform_likes = self.platform_metrics.get('likes_count', 0) if self.platform_metrics else 0
        return platform_likes + self.likes_count
    
    @property
    def total_comments_count(self):
        platform_comments = self.platform_metrics.get('comments_count', 0) if self.platform_metrics else 0
        return platform_comments + self.comments_count
    
    @property
    def total_reshares_count(self):
        platform_reshares = self.platform_metrics.get('reshares_count', 0) if self.platform_metrics else 0
        return platform_reshares + self.reshares_count
