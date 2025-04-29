from typing import Optional
from sqlalchemy import select
from app.db.repositories.base import BaseRepository
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate
from sqlalchemy.ext.asyncio import AsyncSession

class SessionRepository(BaseRepository[Session, SessionCreate, SessionUpdate]):
    def __init__(self, db: AsyncSession):
            super().__init__(model=Session, db=db)

    async def get_by_token(self, *, token: str) -> Optional[Session]:
        statement = select(self.model).where(self.model.token == token)
        result = await self.db.execute(statement)
        return result.scalars().first()
    
    async def get_by_id(self, *, user_id: str) -> Optional[Session]:
        statement = select(self.model).where(self.model.token == user_id)
        result = await self.db.execute(statement)
        return result.scalars().first()
