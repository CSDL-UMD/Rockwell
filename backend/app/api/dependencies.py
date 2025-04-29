from datetime import datetime
from typing import Annotated, Dict

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.user import UserService
from app.services.session import SessionService

security = HTTPBearer()

async def get_session_service(db: AsyncSession = Depends(get_db)):
    """
    Get session service instance
    """
    from app.services.session import SessionService

    return SessionService(db)

async def get_user_service(db: AsyncSession = Depends(get_db)):
    """
    Get user service instance
    """
    from app.services.user import UserService

    return UserService(db)

async def get_current_user(
    request: Request,
    session_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db), 
    userService: UserService = Depends(get_user_service),
    sessionService: SessionService = Depends(get_session_service)
) -> Dict:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    session = await sessionService.get_by_token(token=session_token)

    if not session or session["expiry"]< datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    user = await userService.get_by_id(user_id = session["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Return user for use in route handlers
    return user

async def get_current_admin_user(
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """
    Validate that the user is an admin
    """
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user

async def get_recsys_service(db: AsyncSession = Depends(get_db)):
    """
    Get recommendation system service instance
    """
    from app.services.recsys import RecsysService

    return RecsysService(db)

