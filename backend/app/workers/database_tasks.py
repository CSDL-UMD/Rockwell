import os
import json
import asyncio
from app.core.config import settings
from app.services.post import PostService
from app.db.session import get_db
from app.models.post import PlatformType

HOME = os.path.dirname(__file__) + "/../../"
DB_URL = "./test.db"

async def import_sample_posts():
    """Import sample posts using the PostService"""
    try:
        # Load sample tweets
        with open(HOME + "sample_posts.json", "r") as f:
            tweets_data = json.load(f)
        
        if isinstance(tweets_data, dict) and "data" in tweets_data:
            tweets = tweets_data["data"][:20]
        else:
            tweets = tweets_data  # Assuming direct array of tweets
        
        # Get database session - make sure this is working correctly
        db_generator = get_db()
        db = await anext(db_generator)
        
        try:
            # Create post service with the db session
            post_service = PostService(db)
            
            # Import tweets
            imported_posts = await post_service.import_external_posts(tweets, PlatformType.TWITTER)
            print(f"Successfully imported {len(imported_posts)} sample posts")
        finally:
            # Make sure to close the session
            await db.close()
            
    except Exception as e:
        print(f"Error importing sample posts: {e}")
        # Print more detailed traceback for debugging
        import traceback
        traceback.print_exc()
