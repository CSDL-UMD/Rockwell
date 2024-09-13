import re
import math
import glob
import gzip
import json
import requests
import joblib
import random
import aiohttp
import asyncio
import numpy as np
import pandas as pd
import logging
from itertools import groupby
import threading
import surprise
from collections import Counter
from collections import defaultdict
from argparse import ArgumentParser

LOG_FMT_DEFAULT='%(asctime)s:%(levelname)s:%(message)s'
LOG_PATH_DEFAULT="./prediction_cronjob.log"


def make_logger(path=LOG_PATH_DEFAULT):
    """ 
    By default, log to file messages at level INFO or above. By default, the
    log file will be located in same location from where the script is being
    called. It also adds a stream handler for logging to the console messages
    at level ERROR and above; these will be logged to stderr.
    """
    logging.basicConfig(filename=path,
                        format=LOG_FMT_DEFAULT,
                        filemode='a',
                        level="INFO")
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter(LOG_FMT_DEFAULT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def make_parser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("proj_dir", help="directory with data files")
    return parser

def filter_tweets(feedtweets):
    level_1_tweets = []
    level_2_retweeted = []
    filtered_feedtweets = []
    for tweet in feedtweets:
        unique = False
        no_reply = True
        if tweet["id_str"] not in level_1_tweets:
            if "retweeted_status" in tweet.keys():
                if tweet["retweeted_status"]["id_str"] not in level_1_tweets and tweet["retweeted_status"]["id_str"] not in level_2_retweeted:
                    level_1_tweets.append(tweet["id_str"])
                    level_2_retweeted.append(tweet["retweeted_status"]["id_str"])
                    unique = True
            else:
                level_1_tweets.append(tweet["id_str"])
                unique = True
        if tweet["in_reply_to_status_id_str"]:
            reply = False
        if unique and no_reply:
            filtered_feedtweets.append(tweet)
    return filtered_feedtweets

def break_timeline_attention(public_tweets,public_tweets_score,absent_tweets,max_pages):
    db_tweet_payload = []
    db_tweet_attn_payload = []
    absent_tweets_ids = []
    rankk = 0
    tweetids_by_page = defaultdict(list)
    print(absent_tweets)
    all_tweet_ids = [tweet['id'] for tweet in public_tweets if type(tweet) != float]
    for (i,tweet) in enumerate(public_tweets):
        if type(tweet) == float:
                continue
        page = int(rankk/10)
        rank_in_page = (rankk%10) + 1
        db_tweet = {
            'fav_before':str(tweet['favorited']),
            'tid':str(tweet["id"]),
            'rtbefore':str(tweet['retweeted']),
            'page':page,
            'rank':rank_in_page,
            'predicted_score':public_tweets_score[i]
        }
        db_tweet_payload.append(db_tweet)
        tweetids_by_page[page].append(tweet["id"])
        rankk = rankk + 1

    for tweet in absent_tweets:
        if type(tweet) == float:
                continue
        absent_tweets_ids.append(tweet["id_str"])

    for attn_page in range(max_pages):
        present_tweets_ids = tweetids_by_page[attn_page]
        present_tweets_select = np.random.choice(present_tweets_ids,size=3,replace=False)
        absent_tweets_select = np.random.choice(absent_tweets_ids,size=2,replace=False)
        for absent_tweet_id in absent_tweets_select:
            absent_tweets_ids.remove(absent_tweet_id)
        all_attn_tweets = np.concatenate((present_tweets_select,absent_tweets_select),axis=0)
        np.random.shuffle(all_attn_tweets)
        for (attn_rank,tt) in enumerate(all_attn_tweets):
            present = False
            if tt in present_tweets_select:
                present = True
            db_tweet_attn = {
                'tweet_id':str(tt),
                'page':str(attn_page),
                'rank':str(attn_rank),
                'present':present
            }
            db_tweet_attn_payload.append(db_tweet_attn)
    return db_tweet_payload,db_tweet_attn_payload

def main(proj_dir,log_path=LOG_PATH_DEFAULT):
    logger = make_logger(log_path)
    logger.info(f"Prediction Cron job started: {proj_dir=}")

    try:
        unprocessed_json = {}
        with open(proj_dir+"/configuration/unprocessed.json") as fin:
            unprocessed_json = json.loads(fin.read())
        unprocessed_home_files = unprocessed_json["hometimeline"]

        processed_json = {}
        with open(proj_dir+"/configuration/processed.json") as fin:
            processed_json = json.loads(fin.read())
        processed_home_files = processed_json["hometimeline"]

        new_home_timeline_files = [ff for ff in unprocessed_home_files if ff not in processed_home_files]

        print(new_home_timeline_files)

        for fn in new_home_timeline_files:
            with gzip.open(fn, 'r') as fin:
                data = json.loads(fin.read().decode('utf-8'))
                if data['homeTweets']:
                	feed_tweets = data['homeTweets']
                	feed_tweets = filter_tweets(feed_tweets)
                	db_tweet_payload = []
                	for tweet in feed_tweets:
                                db_tweet = {'tweet_id':tweet["id"],'tweet_json':tweet}
                                db_tweet_payload.append(db_tweet)
                	worker_id = data['worker_id']
                	screenname = data["userObject"]["screen_name"]
                	db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page=NA&feedtype=S")
                	if db_response.json()['data'] != "NEW":
                		existing_tweets = [response[6] for response in db_response.json()['data']]
                		feed_tweets.extend(existing_tweets)

                	feed_tweets = feed_tweets[0:len(feed_tweets)-10]
                	absent_tweets = feed_tweets[-10:]

                	feed_tweets_chronological = []
                	feed_tweets_chronological_score = []
                	for tweet in feed_tweets:
                		feed_tweets_chronological.append(tweet)
                		feed_tweets_chronological_score.append(-100)

                	#timeline_json = [feed_tweets,feed_tweets,screenname]
                	#recsys_response = requests.get('http://127.0.0.1:5053/recsys_rerank',json=timeline_json)
                	#feed_tweets_control = recsys_response.json()['data'][0]
                	#feed_tweets_control_score = recsys_response.json()['data'][1]

                	max_pages = min([len(feed_tweets),5])

                	db_tweet_chronological_payload,db_tweet_chronological_attn_payload = break_timeline_attention(feed_tweets_chronological,feed_tweets_chronological_score,absent_tweets,max_pages)
                	#db_tweet_control_payload,db_tweet_control_attn_payload = break_timeline_attention(feed_tweets_control,feed_tweets_control_score,absent_tweets,max_pages)

                	finalJson = []
                	finalJson.append(db_tweet_payload)
                	finalJson.append(db_tweet_chronological_payload)
                	finalJson.append(db_tweet_chronological_attn_payload)
                	finalJson.append(db_tweet_chronological_payload)
                	finalJson.append(db_tweet_chronological_attn_payload)
                	finalJson.append(worker_id)
                	finalJson.append(screenname)
                	requests.post('http://127.0.0.1:5052/insert_timelines_attention',json=finalJson)

        processed_json["hometimeline"] = unprocessed_home_files
        with open(proj_dir+"/configuration/processed.json","w") as outfile:
        	outfile.write(json.dumps(processed_json))

    except Exception as e:
        logger.error(f"Error in Prediction", exc_info=e)

if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    main(args.proj_dir)