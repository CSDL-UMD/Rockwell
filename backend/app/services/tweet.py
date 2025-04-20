import json
import asyncio
import aiohttp

from html import unescape
from typing import Any, Dict, List, Optional
from dateutil import parser
from pydantic import HttpUrl
from datetime import datetime
from fastapi import HTTPException

from app.models import ContentItem, TwitterEngagements
import app.services.ratelimiter as ratelimiter

import os


class TweetService:
    """Service to handle all tweet operations."""

    def __init__(self, raw_tweets):
        self.tweets = raw_tweets

    async def init_service(self):
        """Initialize the service asynchronously."""
        self.tweets = await self.load_tweets(self.tweets)

    async def load_tweets(self, raw_tweets) -> List[dict]:
        """Load tweets from file into memory asynchronously."""
        try:
            # with open(self.file_path, "r", encoding="utf-8") as fp:
            #     raw_tweets = json.load(fp)["data"][:50]

            preprocessed_tweets = await self.process_data(raw_tweets)

            tweets = [
                self.process_tweet(tweet, idx).dict()
                for idx, tweet in enumerate(preprocessed_tweets)
            ]

            for item in tweets:
                item["url"] = (
                    str(item["url"]) if isinstance(item["url"], HttpUrl) else ""
                )
                item["embeded_image"] = (
                    str(item["embeded_image"])
                    if isinstance(item["embeded_image"], HttpUrl)
                    else ""
                )
                item["created_at"] = (
                    item["created_at"].isoformat()
                    if isinstance(item["created_at"], datetime)
                    else ""
                )

                item["retweet_by"] = item.get("retweet_by", "")
                item["quoted_by"] = item.get("quoted_by", "")
                if item["embeded_images"]:
                    item["embeded_images"] = [
                        str(url) for url in item.get("embeded_images", [])
                    ]

            return tweets

        except FileNotFoundError:
            print()
            print()
            print(os.getcwd(), os.path.dirname(__file__))
            print()
            print()

            exit()
            raise HTTPException(status_code=404, detail="Feed file not found.")

        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid JSON format in feed file."
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_tweets(self) -> List[dict]:
        """Return the list of tweets."""
        return self.tweets

    def find_tweet(self, tweet_id: int) -> Optional[dict]:
        """Find a tweet by its ID."""
        return next(
            (tweet for tweet in self.tweets if tweet["id"] == str(tweet_id)), None
        )

    def like_tweet(self, tweet_id: int) -> dict:
        """Toggle like status for a tweet."""
        tweet = self.find_tweet(tweet_id)
        if tweet is None:
            raise HTTPException(status_code=404, detail="Tweet not found.")

        tweet["engagements"]["liked"] = not tweet["engagements"]["liked"]
        tweet["engagements"]["likes"] += 1 if tweet["engagements"]["liked"] else -1

        return tweet

    def retweet_tweet(self, tweet_id: int) -> dict:
        """Toggle retweet status for a tweet."""
        tweet = self.find_tweet(tweet_id)
        if tweet is None:
            raise HTTPException(status_code=404, detail="Tweet not found.")

        tweet["engagements"]["retweeted"] = not tweet["engagements"]["retweeted"]
        tweet["engagements"]["retweets"] += (
            1 if tweet["engagements"]["retweeted"] else -1
        )
        return tweet

    def _extract_urls(
        self, tweet: Dict[str, Any]
    ) -> tuple[str, Optional[List[HttpUrl]], Optional[List[HttpUrl]]]:
        """Extract URLs from tweet and return cleaned text and list of URLs"""

        # WARN: this thing is supposed to extract urls but why is it stying to get text
        text = tweet["full_text"]
        embedded_urls = []
        media_urls = []

        entities = tweet.get("entities", {})

        # Process URLs
        # if the media url is in the test remove it
        if "urls" in entities:
            for url_dict in entities["urls"]:
                if (
                    not url_dict["expanded_url"].startswith("https://twitter.com/")
                    and url_dict["url"] in text
                ):
                    embedded_urls.append(url_dict["expanded_url"])
                    text = text.replace(url_dict["url"], url_dict["expanded_url"])

                else:
                    text = text.replace(url_dict["expanded_url"], "")
                    text = text.replace(url_dict["url"], "")

        # Process media URLs
        if "media" in entities:
            for media in entities["media"]:
                # WARN: let's replace http with https?
                media_url = media["media_url"].replace("http:", "https:")
                media_urls.append(media_url)
                if "url" in media:
                    # NOTE: remove the url from the media url fromt the text
                    # if it exists, what this part of the processing before
                    text = text.replace(media["url"], "")
                    pass
        return (
            text.strip(),
            embedded_urls if embedded_urls else None,
            media_urls if media_urls else None,
        )

    def _create_engagements(self, tweet: Dict[str, Any]) -> TwitterEngagements:
        """Create TwitterEngagements object from tweet data"""
        return TwitterEngagements(
            retweets=tweet["retweet_count"],
            likes=tweet["favorite_count"],
        )

    # TODO: need to get a better processor this is not goood enough
    async def process_tweet(self, tweet: Dict[str, Any], rank: int) -> ContentItem:
        """Process a single tweet into a ContentItem"""
        # Extract text and URLs
        clean_text, embedded_urls, media_urls = self._extract_urls(tweet)
        embeded_image = media_urls[0] if media_urls and len(media_urls) == 1 else None
        embeded_url = embedded_urls[0] if embedded_urls else None

        # print(f"{embeded_image}, {embeded_url}")
        # raise ValueError (f"{embeded_url}, {embeded_image}")

        # Determine if it's a reply
        is_reply = bool(tweet.get("in_reply_to_status_id_str"))

        # retweet_by = bool(tweet.get("retweeted"))? '' else ''
        # the frontend is the best for readability becasue of all the tenary ops

        # Create ContentItem
        # TODO: the frontend need a lot of stuffs that this does not provide
        # 1 → actor_name → user.name
        # 2 → actor_username → user.screen_name
        # 3 → actor_picture → user.profile_image_url
        # 4 → body → full_text
        # 5 → embedded_image → entities.media[i].media_url (if media exists)
        # 6 → urls → entities.urls[i].expanded_url (if a link exists) what if we have multiple links?
        # 7 → likes → favorite_count
        # 8 → retweet_count → retweet_count
        # 9 → tweet_id → id_str changing this one to id
        # 10 → created_at → created_at

        return ContentItem(
            id=tweet["id_str"],
            text="",
            original_rank=rank,
            body=unescape(clean_text),
            actor_name=tweet["user"]["name"],
            actor_username=tweet["user"]["screen_name"],
            actor_picture=tweet["user"]["profile_image_url"],
            embeded_image=embeded_image,
            url=embeded_url,
            domain_present="",
            type="comment" if is_reply else "post",
            created_at=parser.parse(tweet["created_at"]),
            engagements=self._create_engagements(tweet),
            language=tweet.get("lang"),
            # Optional fields defaulting to None:
            post_id=None,
            parent_id=tweet.get("in_reply_to_status_id_str"),
            title=None,
            embeded_images=media_urls if media_urls and len(media_urls) > 1 else None,
        )

    async def check_url(self, session, url):
        """Check if a URL is accessible."""
        try:
            async with session.head(url, timeout=3) as response:
                return url if response.status < 400 else None
        except:
            return None


    async def process_data(self, data):
        """Scan for URLs, check if they are working, and remove broken ones from the text."""
        urls_to_check = {
            url_info["url"]: url_info["expanded_url"]
            for item in data
            if "entities" in item and "urls" in item["entities"]
            for url_info in item["entities"]["urls"]
        }

        async with aiohttp.ClientSession() as session:
            tasks = [
                self.check_url(session, expanded_url) for expanded_url in urls_to_check.values()
            ]
            results = await asyncio.gather(*tasks)

        working_urls = set(filter(None, results))
        cleaned_data = []

        for item in data:
            if "entities" in item and "urls" in item["entities"]:
                for url_info in item["entities"]["urls"]:
                    if url_info["expanded_url"] not in working_urls:
                        item["full_text"] = item["full_text"].replace(url_info["url"], "")
                item["entities"]["urls"] = [
                    url_info
                    for url_info in item["entities"]["urls"]
                    if url_info["expanded_url"] in working_urls
                ]
            cleaned_data.append(item)

        return cleaned_data
