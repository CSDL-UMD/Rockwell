import os
import pickle
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.repositories import PostRepository

class RecsysService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tweet_repository = PostRepository(self.db)
        self.model = self._load_model()
        self.last_trained = datetime.now()
        
    def _load_model(self):
        """Load ML model from file or initialize a new one"""
        model_path = settings.RECSYS_MODEL_PATH
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        else:
            # Initialize a basic model
            # In a real app, you'd implement a proper ML model
            return {"initialized_at": datetime.now()}
    
    async def get_recommendations(self, user_id: str, count: int = 10) -> List[str]:
        """Get recommended tweet IDs for a user"""
        # If this were a real app, we'd use the model to get personalized recommendations
        # For demo purposes, we'll just return random tweets
        
        # Check if model needs retraining
        if datetime.now() - self.last_trained > timedelta(hours=settings.RECSYS_RETRAIN_INTERVAL):
            await self.retrain_model()
            
        # Get random tweets as recommendations
        tweets = await self.tweet_repository.get_random_tweets(limit=count)
        return [tweet.id for tweet in tweets]
    
    async def record_engagement(self, user_id: str, tweet_id: str, engagement_type: str) -> None:
        """Record user engagement for future model updates"""
        # In a real app, this would update a user-item matrix
        # For now, we'll just log the engagement
        print(f"Recorded {engagement_type} engagement from user {user_id} on tweet {tweet_id}")
    
    async def retrain_model(self) -> None:
        """Retrain the recommendation model with new data"""
        # In a real app, this would use engagement data to train a collaborative filtering model
        print("Retraining recommendation model...")
        self.last_trained = datetime.now()
