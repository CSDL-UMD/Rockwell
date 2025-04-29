from typing import List, Optional, Dict, Tuple
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import joinedload

from app.db.repositories.base import BaseRepository
from app.models.post import Post
from app.models.interaction import Interaction
from app.schemas.post import PostCreate, PostUpdate, InteractionStatus
from sqlalchemy.ext.asyncio import AsyncSession

class PostRepository(BaseRepository[Post, PostCreate, PostUpdate]):
    def __init__(self, db: AsyncSession):
            super().__init__(model=Post, db=db)

    async def get_by_author_id(self, *, author_id: str, skip: int = 0, limit: int = 100) -> List[Post]:
        """Get posts by author ID with pagination"""
        statement = select(self.model).where(
            self.model.author_id == author_id
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(statement)
        return result.scalars().all()
    
    async def get_many_by_ids(self, *, ids: List[str]) -> List[Post]:
        """Get multiple posts by their IDs"""
        statement = select(self.model).where(self.model.id.in_(ids))
        result = await self.db.execute(statement)
        return result.scalars().all()
    
    async def get_with_reference(self, *, id: str) -> Optional[Post]:
        """Get post with its reference post loaded"""
        statement = select(self.model).where(
            self.model.id == id
        ).options(joinedload(self.model.referenced_post))
        result = await self.db.execute(statement)
        return result.scalars().first()
    
    async def get_feed(
        self, 
        *, 
        limit: int = 20, 
        cursor: Optional[str] = None,
        user_id: Optional[str] = None,
        platform_filter: Optional[List[str]] = None
    ) -> Tuple[List[Post], Optional[str]]:
        """
        Get a paginated feed of posts with optional filtering
        Returns posts and the next cursor
        """
        query = select(self.model)
        
        # Apply cursor-based pagination
        if cursor:
            # Assuming cursor is a post ID
            cursor_post = await self.get(id=cursor)
            if cursor_post:
                query = query.where(self.model.created_at < cursor_post.created_at)
        
        # Apply platform filter if provided
        if platform_filter:
            query = query.where(self.model.platform.in_(platform_filter))
        
        # Order and limit
        query = query.order_by(desc(self.model.created_at)).limit(limit + 1)  # +1 to check if there are more
        
        result = await self.db.execute(query)
        posts = result.scalars().all()
        
        # Determine if there are more results and the next cursor
        has_more = len(posts) > limit
        if has_more:
            next_cursor = posts[limit - 1].id
            posts = posts[:limit]
        else:
            next_cursor = None
        
        # Load interaction status for the current user if provided
        if user_id:
            posts = await self.load_interaction_status(posts=posts, user_id=user_id)
        
        return posts, next_cursor
    
    async def get_trending_posts(self, *, limit: int = 20, offset: int = 0) -> List[Post]:
        """Get trending posts based on engagement metrics"""
        # Create a score based on likes, comments, and reshares
        score_expr = (
            (self.model.likes_count * 1) + 
            (self.model.comments_count * 2) + 
            (self.model.reshares_count * 3)
        ).label("score")
        
        query = select(self.model).order_by(desc(score_expr)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def load_interaction_status(self, *, posts: List[Post], user_id: str) -> List[Post]:
        """Load a user's interaction status for a list of posts"""
        if not posts:
            return []
            
        # Get post IDs
        post_ids = [post.id for post in posts]
        
        # Get all interactions for these posts by this user
        interaction_query = select(Interaction).where(
            and_(
                Interaction.post_id.in_(post_ids),
                Interaction.user_id == user_id
            )
        )
        result = await self.db.execute(interaction_query)
        interactions = result.scalars().all()
        
        # Create a dictionary of post_id -> interaction types
        interaction_map = {}
        for interaction in interactions:
            if interaction.post_id not in interaction_map:
                interaction_map[interaction.post_id] = []
            interaction_map[interaction.post_id].append(interaction.interaction_type)
        
        # Update each post with interaction status
        for post in posts:
            interactions = interaction_map.get(post.id, [])
            post.user_liked = "like" in interactions
            post.user_reshared = any(i in ["reshare", "quote"] for i in interactions)
        
        return posts
    
    async def get_interaction_status(self, *, post_ids: List[str], user_id: str) -> Dict[str, InteractionStatus]:
        """Get interaction status for multiple posts for a user"""
        # Query for all interactions by this user for these posts
        interaction_query = select(Interaction).where(
            and_(
                Interaction.post_id.in_(post_ids),
                Interaction.user_id == user_id
            )
        )
        result = await self.db.execute(interaction_query)
        interactions = result.scalars().all()
        
        # Organize by post_id and interaction type
        status_map = {post_id: InteractionStatus(
            post_id=post_id,
            user_liked=False,
            user_commented=False,
            user_reshared=False
        ) for post_id in post_ids}
        
        for interaction in interactions:
            if interaction.interaction_type == "like":
                status_map[interaction.post_id].user_liked = True
            elif interaction.interaction_type in ["comment", "reply"]:
                status_map[interaction.post_id].user_commented = True
            elif interaction.interaction_type in ["reshare", "quote"]:
                status_map[interaction.post_id].user_reshared = True
        
        return status_map
    
    async def create_with_reference(self, *, obj_in: PostCreate, author_id: str) -> Post:
        """Create a post with proper reference handling"""
        post_data = obj_in.dict()
        
        # Determine post type based on reference
        is_reshare = False
        is_quote = False
        is_reply = False
        
        if obj_in.reference_post_id:
            # Check if there's content (quote) or not (reshare)
            if obj_in.content.strip():
                is_quote = True
            else:
                is_reshare = True
            
            # You could also determine if it's a reply based on additional context
            
        # Create post object
        db_obj = self.model(
            **post_data,
            author_id=author_id,
            is_reshare=is_reshare,
            is_quote=is_quote,
            is_reply=is_reply
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def increment_metrics(self, *, post_id: str, metric: str, value: int = 1) -> Optional[Post]:
        """Increment a post's metrics (likes, comments, reshares)"""
        post = await self.get(id=post_id)
        if not post:
            return None
            
        if metric == "likes":
            post.likes_count += value
        elif metric == "comments":
            post.comments_count += value
        elif metric == "reshares":
            post.reshares_count += value
            
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post
    
    async def search_posts(self, *, query: str, limit: int = 20, offset: int = 0) -> List[Post]:
        """Search posts by content"""
        # Basic text search - could be improved with full-text search
        search_query = f"%{query}%"
        statement = select(self.model).where(
            self.model.content.ilike(search_query)
        ).order_by(desc(self.model.created_at)).offset(offset).limit(limit)
        
        result = await self.db.execute(statement)
        return result.scalars().all()
