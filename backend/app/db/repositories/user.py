from typing import Optional
from sqlalchemy import select
from app.db.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):

    def __init__(self, db: AsyncSession):
            super().__init__(model=User, db=db)

    async def get_by_email(self, *, email: str) -> Optional[User]:
        statement = select(self.model).where(self.model.email == email)
        result = await self.db.execute(statement)
        return result.scalars().first()
    
    async def get_by_username(self, *, username: str) -> Optional[User]:
        statement = select(self.model).where(self.model.username == username)
        result = await self.db.execute(statement)
        return result.scalars().first()
    
    async def get_by_twitter_id(self, *, twitter_id: str) -> Optional[User]:
        statement = select(self.model).where(self.model.twitter_id == twitter_id)
        result = await self.db.execute(statement)
        return result.scalars().first()
