from typing import Dict, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash, verify_password
from app.db.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
    
    async def get_by_email(self, *, email: str) -> Optional[Dict]:
        user = await self.repository.get_by_email(email=email)
        if user:
            return self._map_to_dict(user)
        return None
    
    async def get_by_id(self, *, user_id: str) -> Optional[Dict]:
        user = await self.repository.get(id=user_id)
        if user:
            return self._map_to_dict(user)
        return None
    
    async def create(self, *, obj_in: UserCreate) -> Dict:
        hashed_password = get_password_hash(obj_in.password)
        user_create = UserCreate(
            email=obj_in.email,
            username=obj_in.username,
            password=hashed_password
        )
        user = await self.repository.create(obj_in=user_create)
        return self._map_to_dict(user)
    
    async def update(
        self, *, user_id: str, obj_in: Union[UserUpdate, Dict]
    ) -> Optional[Dict]:
        user = await self.repository.get(id=user_id)
        if not user:
            return None
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
        
        user = await self.repository.update(db_obj=user, obj_in=update_data)
        return self._map_to_dict(user)
    
    async def authenticate(
        self, *, email: str, password: str
    ) -> Optional[Dict]:
        user = await self.repository.get_by_email(email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return self._map_to_dict(user)
    
    def _map_to_dict(self, user) -> Dict:
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "twitter_id": user.twitter_id,
            "created_at": user.created_at
        }