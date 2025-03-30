# ruff: noqa: E501

from html import unescape
from typing import Any, Dict, List, Optional

from dateutil import parser
from pydantic import HttpUrl

from rockwell.models import ContentItem, TwitterEngagements


class TwitterFeedProcessor:
    """Processes Twitter feed data into ContentItem format"""

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
    def process_tweet(self, tweet: Dict[str, Any], rank: int) -> ContentItem:
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
