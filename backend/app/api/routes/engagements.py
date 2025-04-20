from fastapi import APIRouter, Request
import requests

from app.services.recsys import RecsysService
import app.services.ratelimiter as ratelimiter 
import logging

# from app.db.repositories.tweet import TweetRepository

router = APIRouter()

router('/retweet_post', methods=['GET','POST'])
def retweet_post(request: Request):
    worker_id = request.args.get('worker_id').strip()
    tweet_id = request.args.get('tweet_id').strip()
    db_response = requests.get('http://127.0.0.1:5052/get_existing_user?worker_id='+str(worker_id))
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    userid = db_response[0][3]

    logging.info(f"Retweet request started for : {userid=}")

    ratelimiter.push_retweet(tweet_id,userid,access_token,access_token_secret)
    return {"success":1} # Retweet successful

router('/like_post', methods=['GET','POST'])
def like_post(request: Request):
    worker_id = request.args.get('worker_id').strip()  
    tweet_id = request.args.get('tweet_id').strip()  
    db_response = requests.get('http://127.0.0.1:5052/get_existing_user?worker_id='+str(worker_id))
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    userid = db_response[0][3]

    logging.info(f"Like request started for : {userid=}")

    ratelimiter.push_like(tweet_id,userid,access_token,access_token_secret)
    return {"success":1} # Like successful
