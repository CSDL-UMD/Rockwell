from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generator, Optional, Dict

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.schemas.token import TokenPayload
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Validate access token and return current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    
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