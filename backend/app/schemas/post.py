from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# Base Models
class UserRef(BaseModel):
    id: str
    username: str

# Post Models
class PostBase(BaseModel):
    content: str
    media_urls: Optional[List[str]] = None  # Just URLs for images to display
    reference_post_id: Optional[str] = None
    
class PostCreate(PostBase):
    platform: str = "internal"
    
class PostUpdate(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None

class ReferencePost(BaseModel):
    id: str
    snippet: str
    author: UserRef

class PostResponse(BaseModel):
    id: str
    author: UserRef
    content: str
    media_urls: Optional[List[str]] = None  # Simple list of image URLs
    created_at: datetime
    updated_at: Optional[datetime] = None
    platform: str
    external_id: Optional[str] = None
    
    # Post type information
    is_reshare: bool = False
    is_quote: bool = False
    is_reply: bool = False
    reference_post: Optional[ReferencePost] = None
    
    # Engagement metrics
    likes_count: int = 0
    comments_count: int = 0
    reshares_count: int = 0
    
    # User-specific interactions
    user_liked: bool = False
    user_reshared: bool = False
    
    # Additional data
    platform_data: Optional[Dict[str, Any]] = None
    ranking_score: Optional[float] = None
    is_attention_check: bool = False
    
    class Config:
        from_attributes = True

# Feed Models
class FeedItem(PostResponse):
    feed_position: int
    
class FeedResponse(BaseModel):
    items: List[FeedItem]
    next_cursor: Optional[str] = None
    has_more: bool = False


class CommentCreate(BaseModel):
    content: str
    media_urls: Optional[List[str]] = None  # Simple list of image URLs
    parent_comment_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    post_id: str
    author: UserRef
    content: str
    media_urls: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    parent_comment_id: Optional[str] = None
    likes_count: int = 0
    replies_count: int = 0
    user_liked: bool = False
    
    class Config:
        from_attributes = True

class LikeResponse(BaseModel):
    post_id: str
    liked: bool
    likes_count: int

class ReshareCreate(BaseModel):
    content: Optional[str] = None  # If provided, it's a quote; if not, it's a reshare
    media_urls: Optional[List[str]] = None

class ReshareResponse(BaseModel):
    original_post_id: str
    new_post_id: Optional[str] = None  # Will be populated for quotes
    reshared: bool
    reshares_count: int

# Interaction Status
class InteractionStatus(BaseModel):
    post_id: str
    user_liked: bool
    user_commented: bool
    user_reshared: bool
    
class BatchInteractionStatusRequest(BaseModel):
    post_ids: List[str]

class BatchInteractionStatusResponse(BaseModel):
    statuses: List[InteractionStatus]

