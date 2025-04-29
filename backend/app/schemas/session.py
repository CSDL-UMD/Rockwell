from pydantic import BaseModel
from app.core.security import session_expiry
from datetime import datetime

class SessionCreate(BaseModel):
    token: str
    user_id: str
    expires: datetime = session_expiry(hours=24)
    # token_type: str = "bearer"

class SessionUpdate(BaseModel):
    user_id: str

class SessionDelete(BaseModel):
    user_id: str

