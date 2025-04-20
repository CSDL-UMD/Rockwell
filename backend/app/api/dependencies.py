from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator, Optional, Dict

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.services.user import UserService


async def get_current_user(
) -> Dict:
    """
    Validate access token and return current user
    """


    
    
    return user

async def get_current_active_user(
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """
    Validate that the user is active
    """
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """
    Validate that the user is an admin
    """
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions"
        )
    return current_user

async def get_recsys_service(db: AsyncSession = Depends(get_db)):
    """
    Get recommendation system service instance
    """
    from app.services.recsys import RecsysService
    return RecsysService(db)