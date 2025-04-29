from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    Response,
    status,
)

# from requests_oauthlib import OAuth1Session
# from fastapi.security import OAuth2PasswordRequestForm
# from fastapi.responses import HTMLResponse
# from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_session_service, get_user_service
from app.core.config import settings
from app.core.security import session_expiry, verify_password
from app.db.session import get_store
from app.schemas import SessionCreate, UserCreate

# import logging
from app.services import SessionService, UserService

router = APIRouter()

app = FastAPI()

@app.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    userService: UserService = Depends(get_user_service), 
    sessionService: SessionService = Depends(get_session_service) 
):

    user_dict = UserService.get_by_username(username)
    if not user_dict or not verify_password(password, user_dict["pwd_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    

    session_create = SessionCreate(
        user_id=user_dict["id"],
        expires=session_expiry(hours=24) 
    )

    session = await sessionService.create(obj_in=session_create) 

    response.set_cookie(
        "session_token",
        session["token"],
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=24*3600,
    )
    return {"message": "Logged in"}

@app.post("/signup")
async def create(
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    userService: UserService = Depends(get_user_service), 
    sessionService: SessionService = Depends(get_session_service) 
):

    user_dict = UserService.get_by_username(username)
    if user_dict:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User already exists.")

    user_create = UserCreate(
        email = "",
        username = username,
        password = password
    ) 

    user_dict = userService.create(user_create)
    
    session_create = SessionCreate(
        user_id=user_dict["id"],
        expires=session_expiry(hours=24) 
    )

    session = await sessionService.create(obj_in=session_create) 

    response.set_cookie(
        "session_token",
        session["token"],
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=24*3600,
    )
    return {"message": "Signed up"}
