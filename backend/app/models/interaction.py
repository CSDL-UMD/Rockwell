import enum
import uuid

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class InteractionType(enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    RESHARE = "reshare"
    QUOTE = "quote"

# Unified interaction model for likes, comments, and reshares
class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Who performed the interaction
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # What post was interacted with
    post_id = Column(String, ForeignKey("posts.id"), nullable=False)
    
    # What type of interaction
    interaction_type = Column(Enum(InteractionType), nullable=False)
    
    # Content (for comments/quotes)
    content = Column(Text, nullable=True)
    
    # Media (for comments/quotes)
    media_urls = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # For comments/replies to comments
    parent_interaction_id = Column(String, ForeignKey("interactions.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    post = relationship("Post", back_populates="interactions")
    parent_interaction = relationship("Interaction", remote_side=[id], backref="replies")
    
    # Ensure a user can only like a post once
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", "interaction_type", 
                         name="unique_user_post_interaction_type"),
    )
