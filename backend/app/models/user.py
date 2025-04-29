import uuid
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    twitter_id = Column(String, unique=True, nullable=True)
    twitter_access_token = Column(String, nullable=True)
    twitter_access_secret = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    posts = relationship("Post", back_populates="author")
    
    # Updated relationship to use the unified Interaction model
    interactions = relationship("Interaction", back_populates="user")
    
    # Optional: helper properties to filter interactions by type
    @property
    def likes(self):
        return [i for i in self.interactions if i.interaction_type.value == "like"]
    
    @property
    def comments(self):
        return [i for i in self.interactions if i.interaction_type.value == "comment"]
    
    @property
    def reshares(self):
        return [i for i in self.interactions if i.interaction_type.value in ["reshare", "quote"]]
