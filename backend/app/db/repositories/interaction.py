from typing import List, Optional, Any, Tuple
from sqlalchemy import select, desc, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.interaction import Interaction

class InteractionRepository(BaseRepository[Interaction, Any, Any]):
    """Repository for handling post interactions"""

    def __init__(self, db: AsyncSession):
            super().__init__(model=Interaction, db=db)
    
    async def create_like(self, *, user_id: str, post_id: str) -> Tuple[Interaction, bool]:
        """Create or remove a like interaction"""
        # Check if like already exists
        statement = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.post_id == post_id,
                self.model.interaction_type == "like"
            )
        )
        result = await self.db.execute(statement)
        existing = result.scalars().first()
        
        if existing:
            # Unlike - remove the interaction
            await self.db.delete(existing)
            await self.db.commit()
            return existing, False
        else:
            # Create new like
            like = self.model(
                user_id=user_id,
                post_id=post_id,
                interaction_type="like"
            )
            self.db.add(like)
            await self.db.commit()
            await self.db.refresh(like)
            return like, True
    
    async def create_comment(self, *, user_id: str, post_id: str, content: str, 
                           media_urls: Optional[List[str]] = None,
                           parent_id: Optional[str] = None) -> Interaction:
        """Create a comment interaction"""
        comment = self.model(
            user_id=user_id,
            post_id=post_id,
            interaction_type="comment" if not parent_id else "reply",
            content=content,
            media_urls=media_urls,
            parent_interaction_id=parent_id
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
    
    async def get_comments(self, *, post_id: str, parent_id: Optional[str] = None, 
                         limit: int = 20, offset: int = 0) -> List[Interaction]:
        """Get comments for a post, optionally filtered by parent comment"""
        query = select(self.model).where(
            and_(
                self.model.post_id == post_id,
                self.model.interaction_type.in_(["comment", "reply"])
            )
        )
        
        if parent_id is not None:
            query = query.where(self.model.parent_interaction_id == parent_id)
        else:
            query = query.where(self.model.parent_interaction_id is None)
            
        query = query.order_by(desc(self.model.created_at)).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create_reshare(self, *, user_id: str, post_id: str, 
                           content: Optional[str] = None,
                           media_urls: Optional[List[str]] = None) -> Interaction:
        """Create a reshare or quote interaction"""
        interaction_type = "quote" if content else "reshare"
        
        reshare = self.model(
            user_id=user_id,
            post_id=post_id,
            interaction_type=interaction_type,
            content=content,
            media_urls=media_urls
        )
        self.db.add(reshare)
        await self.db.commit()
        await self.db.refresh(reshare)
        return reshare
    
    async def check_interaction_exists(self, *, user_id: str, post_id: str, 
                                    interaction_type: str) -> bool:
        """Check if a specific interaction exists"""
        statement = select(exists().where(
            and_(
                self.model.user_id == user_id,
                self.model.post_id == post_id,
                self.model.interaction_type == interaction_type
            )
        ))
        result = await self.db.execute(statement)
        return result.scalar()
