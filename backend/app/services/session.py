from typing import Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_session_token, session_expiry 
from app.db.repositories.session import SessionRepository
from app.schemas.session import SessionCreate, SessionUpdate

class SessionService:
    def __init__(self, db: AsyncSession):
        self.repository = SessionRepository(db)

    async def get_by_token(self, *, token: str) -> Optional[Dict]:
        token = await self.repository.get_by_token(token=token)
        if token:
            return self._map_to_dict(token)
        return None
    
    async def get_by_id(self, *, user_id: str) -> Optional[Dict]:
        token = await self.repository.get(id=user_id)
        if token:
            return self._map_to_dict(token)
        return None
    
    async def create(self, *, obj_in: SessionCreate) -> Dict:

        token = create_session_token()
        session_create = SessionCreate(
            token=token,
            user_id=obj_in.user_id,
            expires=session_expiry(hours=24),
        )

        session = await self.repository.create(obj_in=session_create)
        return self._map_to_dict(session)
    
    def _map_to_dict(self, session) -> Dict:
        return {
            "user_id": session.user_id,
            "created_at": session.created,
            "token": session.token,
            "expires": session.expires,
    }
