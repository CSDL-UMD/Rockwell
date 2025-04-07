from typing import List, Optional
from sqlalchemy import select, func, desc
from app.db.repositories.base import BaseRepository
from app.models.tweet import Tweet
from app.schemas.tweet import TweetCreate, TweetBase

class TweetRepository(BaseRepository[Tweet, TweetCreate, TweetBase]):
    async def get_by_author_id(self, *, author_id: str, skip: int = 0, limit: int = 100) -> List[Tweet]:
        statement = select(self.model).where(
            self.model.author_id == author_id
        ).order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(statement)
        return result.scalars().all()
    
    async def get_many_by_ids(self, *, ids: List[str]) -> List[Tweet]:
        statement = select(self.model).where(self.model.id.in_(ids))
        result = await self.db.execute(statement)
        return result.scalars().all()
    
    async def get_random_tweets(self, *, limit: int = 10) -> List[Tweet]:
        # Note: Implementation depends on database (this is for PostgreSQL)
        statement = select(self.model).order_by(func.random()).limit(limit)
        result = await self.db.execute(statement)
        return result.scalars().all()