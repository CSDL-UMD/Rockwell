import json
from typing import List, Dict
from app.services.recsys import RecsysService
from app.services.tweet import TweetService
from app.db.session import get_store
import random


class FeedGenerationService:
    def __init__(self,recsys_service: RecsysService):
        self.recsys_service = recsys_service
    
    async def generate_feed(self, user_id: str, count: int = 10, include_attention_checks: bool = True) -> List[Dict]:
        """Generate a personalized feed for a user"""

        # Get recommendations from the recommendation system
        # tweet_ids = await self.recsys_service.get_recommendations(user_id, count=count)

        # tweet_ids = []
        tweets = await self.tweet_repository.get_tweets_by_ids(tweet_ids)
        # Mocking the tweet repository call  

        # Fetch the full tweet objects
        with open ('backend/app/db/tweets.json', 'r') as f:
            tweets = json.load(f)["data"]

        tweet_services_store = get_store("tweet_services_store")
        if user_id in tweet_services_store.keys():
            tweet_service = tweet_services_store[user_id]
        else:
            tweet_service = TweetService(tweets)
            await tweet_service.init_service()
            tweet_services_store[user_id] = tweet_service 
        
        feed_items = tweet_service.get_tweets()
        
        # Add attention checks if needed
        if include_attention_checks and len(feed_items) >= 5:
            attention_check_position = random.randint(2, min(count - 2, len(feed_items) - 2))
            attention_check = await self._create_attention_check()
            feed_items.insert(attention_check_position, attention_check)
        
        # Truncate to requested count in case we added attention checks
        return feed_items[:count]
    
    async def _create_attention_check(self) -> Dict:
        """Create an attention check tweet"""
        # Get a random real tweet as a template
        random_tweets = await self.tweet_repository.get_random_tweets(limit=1)
        if not random_tweets:
            return self._create_default_attention_check()
        
        template = random_tweets[0]
        
        # Create attention check based on the template
        return {
            "id": f"attention-{template.id}",
            "author_id": template.author_id,
            "content": "ATTENTION CHECK: Please retweet this post",
            "created_at": template.created_at,
            "likes_count": template.likes_count,
            "retweets_count": template.retweets_count,
            "replies_count": template.replies_count,
            "media_urls": template.media_urls,
            "metadata": {"attention_check": True, "original_id": template.id},
            "ranking_score": 1.0,  # High score to ensure visibility
            "is_attention_check": True
        }
    
    def _create_default_attention_check(self) -> Dict:
        """Create a default attention check when no template is available"""
        from datetime import datetime
        
        return {
            "id": "attention-default",
            "author_id": "attention-system",
            "content": "ATTENTION CHECK: Please retweet this post to show you're paying attention",
            "created_at": datetime.now(),
            "likes_count": 0,
            "retweets_count": 0,
            "replies_count": 0,
            "media_urls": [],
            "metadata": {"attention_check": True},
            "ranking_score": 1.0,
            "is_attention_check": True
        }
