from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import PostRepository, InteractionRepository
import json

from app.schemas.post import (
    PostCreate,
    PostUpdate,
    CommentCreate,
    ReshareCreate,
)
from app.models.post import Post, PlatformType
from app.models.interaction import Interaction
from enum import Enum


class PostService:
    """Service to handle post operations and interactions."""

    def __init__(self, db: AsyncSession):
        self.repository = PostRepository(db)
        self.interaction_repository = InteractionRepository(db)

    async def get_by_id(
        self, *, post_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Get a post by its ID with optional user interaction status."""
        post = await self.repository.get_with_reference(id=post_id)
        if not post:
            return None

        # Load user interaction status if requested
        if user_id:
            post = (
                await self.repository.load_interaction_status(
                    posts=[post], user_id=user_id
                )
            )[0]

        return self._map_to_response(post, include_reference=True)

    async def get_by_author_id(
        self,
        *,
        author_id: str,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get posts by author ID with pagination."""
        posts = await self.repository.get_by_author_id(
            author_id=author_id, skip=skip, limit=limit
        )

        # Load user interaction status if requested
        if user_id and posts:
            posts = await self.repository.load_interaction_status(
                posts=posts, user_id=user_id
            )

        return [self._map_to_response(post) for post in posts]

    async def get_feed(
        self,
        *,
        limit: int = 20,
        cursor: Optional[str] = None,
        user_id: Optional[str] = None,
        platform_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get a paginated feed of posts."""
        posts, next_cursor = await self.repository.get_feed(
            limit=limit, cursor=cursor, user_id=user_id, platform_filter=platform_filter
        )

        # Map posts to response format
        items = []
        for i, post in enumerate(posts):
            post_dict = self._map_to_response(post)
            post_dict["feed_position"] = i
            items.append(post_dict)

        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        }

    async def create(self, *, obj_in: PostCreate, author_id: str) -> Dict:
        """Create a new post."""
        post = await self.repository.create_with_reference(
            obj_in=obj_in, author_id=author_id
        )
        return self._map_to_response(post, include_reference=True)

    async def update(
        self, *, post_id: str, obj_in: PostUpdate, user_id: str
    ) -> Optional[Dict]:
        """Update a post if the user is the author."""
        post = await self.repository.get(id=post_id)
        if not post or post.author_id != user_id:
            return None

        updated_post = await self.repository.update(db_obj=post, obj_in=obj_in)
        return self._map_to_response(updated_post)

    async def delete(self, *, post_id: str, user_id: str) -> bool:
        """Delete a post if the user is the author."""
        post = await self.repository.get(id=post_id)
        if not post or post.author_id != user_id:
            return False

        await self.repository.delete(id=post_id)
        return True

    async def like_post(self, *, post_id: str, user_id: str) -> Optional[Dict]:
        """Like or unlike a post."""
        post = await self.repository.get(id=post_id)
        if not post:
            return None

        # Create or remove like
        _, liked = await self.interaction_repository.create_like(
            user_id=user_id, post_id=post_id
        )

        # Update metrics
        metric_change = 1 if liked else -1
        updated_post = await self.repository.increment_metrics(
            post_id=post_id, metric="likes", value=metric_change
        )

        return {
            "post_id": post_id,
            "liked": liked,
            "likes_count": updated_post.likes_count,
        }

    async def comment_on_post(
        self, *, post_id: str, user_id: str, comment_data: CommentCreate
    ) -> Optional[Dict]:
        """Add a comment to a post."""
        post = await self.repository.get(id=post_id)
        if not post:
            return None

        # Validate parent comment if provided
        if comment_data.parent_comment_id:
            parent_comment = await self.interaction_repository.get(
                id=comment_data.parent_comment_id
            )
            if not parent_comment or parent_comment.post_id != post_id:
                return None

        # Create comment
        comment = await self.interaction_repository.create_comment(
            user_id=user_id,
            post_id=post_id,
            content=comment_data.content,
            media_urls=comment_data.media_urls,
            parent_id=comment_data.parent_comment_id,
        )

        # Update post metrics
        await self.repository.increment_metrics(
            post_id=post_id, metric="comments", value=1
        )

        # Get user info for response
        # In a real implementation, you'd fetch this from your user service
        user = {"id": user_id, "username": "username"}  # Placeholder

        return {
            "id": comment.id,
            "post_id": post_id,
            "author": user,
            "content": comment.content,
            "media_urls": comment.media_urls,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "parent_comment_id": comment.parent_interaction_id,
            "likes_count": 0,
            "replies_count": 0,
            "user_liked": False,
        }

    async def get_post_comments(
        self,
        *,
        post_id: str,
        parent_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get comments for a post."""
        # Check if post exists
        post = await self.repository.get(id=post_id)
        if not post:
            return []

        # Get comments
        comments = await self.interaction_repository.get_comments(
            post_id=post_id, parent_id=parent_id, limit=limit, offset=offset
        )

        # Map to response format
        result = []
        for comment in comments:
            # Get user info
            # In a real implementation, you'd fetch this from your user service
            user = {"id": comment.user_id, "username": "username"}  # Placeholder

            # Check if user liked this comment
            user_liked = False
            if user_id:
                # Check if user liked this comment
                # This could be optimized for bulk checking
                pass

            result.append(
                {
                    "id": comment.id,
                    "post_id": post_id,
                    "author": user,
                    "content": comment.content,
                    "media_urls": comment.media_urls,
                    "created_at": comment.created_at,
                    "updated_at": comment.updated_at,
                    "parent_comment_id": comment.parent_interaction_id,
                    "likes_count": 0,  # This would come from a count query
                    "replies_count": 0,  # This would come from a count query
                    "user_liked": user_liked,
                }
            )

        return result

    async def reshare_post(
        self,
        *,
        post_id: str,
        user_id: str,
        reshare_data: Optional[ReshareCreate] = None,
    ) -> Optional[Dict]:
        """Reshare or quote a post."""
        # Check if post exists
        original_post = await self.repository.get(id=post_id)
        if not original_post:
            return None

        # Determine if this is a quote (has content) or simple reshare
        is_quote = reshare_data and reshare_data.content

        # Create interaction to track the reshare
        # interaction = await self.interaction_repository.create_reshare(
        #     user_id=user_id,
        #     post_id=post_id,
        #     content=reshare_data.content if reshare_data else None,
        #     media_urls=reshare_data.media_urls if reshare_data else None,
        # )

        await self.interaction_repository.create_reshare(
            user_id=user_id,
            post_id=post_id,
            content=reshare_data.content if reshare_data else None,
            media_urls=reshare_data.media_urls if reshare_data else None,
        )

        # Update metrics on original post
        await self.repository.increment_metrics(
            post_id=post_id, metric="reshares", value=1
        )

        # If it's a quote, create a new post
        new_post_id = None
        if is_quote:
            # Create new post with reference to original
            new_post = await self.repository.create_with_reference(
                obj_in=PostCreate(
                    content=reshare_data.content,
                    media_urls=reshare_data.media_urls,
                    reference_post_id=post_id,
                    platform="internal",
                ),
                author_id=user_id,
            )
            new_post_id = new_post.id

        return {
            "original_post_id": post_id,
            "new_post_id": new_post_id,
            "reshared": True,
            "reshares_count": original_post.reshares_count + 1,
        }

    async def get_interaction_status(
        self, *, post_ids: List[str], user_id: str
    ) -> Dict[str, Dict]:
        """Get interaction status for multiple posts."""
        status_map = await self.repository.get_interaction_status(
            post_ids=post_ids, user_id=user_id
        )

        return {"statuses": [status.dict() for status in status_map.values()]}

    def _map_to_response(self, post: Post, include_reference: bool = False) -> Dict:
        """Map database post model to response dictionary."""
        result = {
            "id": post.id,
            "author": {
                "id": post.author_id,
                "username": "username",  # This should come from author relation
            },
            "content": post.content,
            "media_urls": post.media_urls,
            # "created_at": post.created_at,
            # "updated_at": post.updated_at,
            "platform": post.platform,
            "external_id": post.external_id,
            # "is_reshare": post.is_reshare,
            # "is_quote": post.is_quote,
            # "is_reply": post.is_reply,
            # "likes_count": post.likes_count,
            # "comments_count": post.comments_count,
            # "reshares_count": post.reshares_count,
            "user_liked": getattr(post, "user_liked", False),
            "user_reshared": getattr(post, "user_reshared", False),
            "platform_metrics": post.platform_metrics,
            "ranking_score": getattr(post, "ranking_score", None),
            "is_attention_check": getattr(post, "is_attention_check", False),
            "reference_post": None,
        }

        # Include reference post if requested and available
        if (
            include_reference
            and post.reference_post_id
            and hasattr(post, "referenced_post")
        ):
            ref = post.referenced_post
            result["reference_post"] = {
                "id": ref.id,
                "snippet": ref.content[:100] + "..."
                if len(ref.content) > 100
                else ref.content,
                "author": {
                    "id": ref.author_id,
                    "username": "username",  # This should come from author relation
                },
            }

        return result

    # Methods for importing from external platforms
    async def import_external_posts(
        self, posts: List[Dict], platform: Enum
    ) -> List[Dict]:
        """Import posts from external platforms."""
        imported_posts = []

        for post_data in posts:
            # Process based on platform
            if platform == PlatformType.TWITTER:
                post_dict = self._process_twitter_post(post_data)
            elif platform == PlatformType.FACEBOOK:
                post_dict = self._process_facebook_post(post_data)
            else:
                continue

            # print(post_dict)
            # Remove interaction count fields that are calculated properties
            # print(post_dict)
            # print(type(post_dict['created_at']))
            # print(post_dict['created_at'].tzinfo)
            # assert(isinstance(post_dict['created_at'], datetime))
            # print(Post.__mapper__.c.keys())
            # assert(post_dict['created_at'].tzinfo is not None)


            # Create post in database
            post = await self.repository.create(obj_in=post_dict)
            print("Done")
            print(post)
            imported_posts.append(self._map_to_response(post))

        return imported_posts

    def _process_twitter_post(self, tweet: Dict) -> Dict:
        """Process a Twitter post into our model."""
        # Extract media URLs
        media_urls = []
        if "entities" in tweet and "media" in tweet["entities"]:
            for media in tweet["entities"]["media"]:
                media_url = media.get("media_url_https", media.get("media_url"))
                if media_url:
                    media_urls.append(media_url)

        # Determine post type
        is_reply = bool(tweet.get("in_reply_to_status_id_str"))
        is_quote = bool(tweet.get("quoted_status_id_str"))
        is_retweet = tweet.get("retweeted_status") is not None

        # Get reference post ID if needed
        reference_post_id = None
        if is_retweet and "retweeted_status" in tweet:
            reference_post_id = tweet["retweeted_status"]["id_str"]
        elif is_quote and "quoted_status_id_str" in tweet:
            reference_post_id = tweet["quoted_status_id_str"]

            # datetime.strptime(
            #     tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y"
            # ),
        # Create post dict
        return {
            "external_id": tweet["id_str"],
            "platform": "TWITTER",
            "content": tweet["full_text"] if "full_text" in tweet else tweet["text"],
            # "created_at": datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")),
            # "created_at": datetime.now(),
            # "created_at": datetime.strptime(tweet["created_at"].split(".")[0], "%Y-%m-%dT%H:%M:%S"),
            # "created_at": str(datetime.now()),
            # "created_at": datetime.date(),
            # "updated_at": datetime.now(),
            "media_urls": json.dumps(media_urls),
            # "is_reply": is_reply,
            # "is_quote": is_quote,
            # "is_reshare": is_retweet,
            'author_id' : "system_import_user",
            "platform_metrics": {
                "likes_count": tweet.get("favorite_count", 0),
                "comments_count": 0,  # Twitter API doesn't provide this directly
                "reshares_count": tweet.get("retweet_count", 0),
            },
            "reference_post_id": reference_post_id,
            "external_author_id": "nope",
            "external_author_name": tweet["user"]["name"],
            "external_author_username": tweet["user"]["screen_name"],
            # "platform_data": tweet,
        }

