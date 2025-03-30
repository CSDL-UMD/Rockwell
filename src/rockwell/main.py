from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from rockwell.services import TweetService
import os

app = FastAPI()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

tweet_service = TweetService()


@app.on_event("startup")
async def startup_event():
    """Initialize the tweet service when the app starts."""
    await tweet_service.init_service()


@app.get("/")
async def home(request: Request):
    """Render the homepage with tweets."""
    tweets = tweet_service.get_tweets()
    return templates.TemplateResponse(
        "index.html", {"request": request, "tweets": tweets}
    )


@app.get("/feed", response_model=list)
async def get_feed():
    """Returns the processed tweet feed."""
    return JSONResponse(content=tweet_service.get_tweets())


@app.post("/like/{tweet_id}")
async def like_tweet(request: Request, tweet_id: int):
    """Handles liking a tweet."""
    tweet = tweet_service.like_tweet(tweet_id)
    return templates.TemplateResponse(
        "like_button.html", {"request": request, "tweet": tweet}
    )


@app.post("/retweet/{tweet_id}")
async def retweet_tweet(request: Request, tweet_id: int):
    """Handles retweeting a tweet."""
    tweet = tweet_service.retweet_tweet(tweet_id)
    return templates.TemplateResponse(
        "retweet_button.html", {"request": request, "tweet": tweet}
    )
