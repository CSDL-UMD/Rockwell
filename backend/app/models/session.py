from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

# class User(Base):
#     __tablename__ = "users"
#     id       = Column(Integer, primary_key=True)
#     username = Column(String, unique=True, index=True)
#     pwd_hash = Column(String)

class Session(Base):
    __tablename__ = "sessions"
    token     = Column(String, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"))
    created   = Column(DateTime, default=datetime.utcnow)
    expires   = Column(DateTime)
    user      = relationship("User")

