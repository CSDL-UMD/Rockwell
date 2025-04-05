from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from rockwell.services import TweetService
import psycopg2
import json
import os

app = FastAPI()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

tweet_service = TweetService()

DB_URL = os.getenv("DATABASE_URL")

APP_HOME = os.path.dirname(__file__) + "/../../"

def run_schema_sql(conn):
    with conn.cursor() as cur:
        with open(APP_HOME + "schema.sql", "r") as f:
            cur.execute(f.read())
        conn.commit()

def insert_sample_tweets(conn):
    with open(APP_HOME + "sample_posts.json", "r") as f:
        tweets = json.load(f)["data"]
    
    with conn.cursor() as cur:
        for tweet in tweets:
            cur.execute("""
                INSERT INTO tweets (id, data)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (int(tweet["id"]), json.dumps(tweet)))
        conn.commit()

def get_tweets_from_db(conn, number):
    cur = conn.cursor()
    
    cur.execute(f"SELECT data FROM tweets ORDER BY id DESC LIMIT {number};")
    rows = cur.fetchall()

    cur.close()

    return [row[0] for row in rows]

@app.on_event("startup")
async def init():
    """Initialize the database service when the app starts."""
    conn = psycopg2.connect(DB_URL)
    run_schema_sql(conn)
    insert_sample_tweets(conn)
    await tweet_service.init_service(get_tweets_from_db(conn, 40))
    conn.close()


# @app.on_event("startup")
# async def init_tweet_service():
#     """Initialize the tweet service when the app starts."""
#     await tweet_service.init_service()


@app.get("/tweets")
def get_tweets():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT data FROM tweets ORDER BY id DESC LIMIT 15;")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Each row is a tuple like: (data,)
    return [row[0] for row in rows]


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
