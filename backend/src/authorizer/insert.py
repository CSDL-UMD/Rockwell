import os
import glob
import re
import gzip
import html
import numpy as np
from dateutil import parser
from flask import Flask, render_template, request, url_for, redirect, flash, make_response, jsonify
import requests
import random, string
import datetime
from requests_oauthlib import OAuth1Session
#from src.databaseAccess.database_config import config
from configparser import ConfigParser
from collections import defaultdict
import logging
import psycopg2
import json
import glob
import xml
import xml.sax.saxutils

def filter_tweets(feedtweetsv1,feedtweetsv2):
    print(len(feedtweetsv1))
    print(len(feedtweetsv2))
    level_1_tweets = []
    level_2_retweeted = []
    filtered_feedtweets = []
    filtered_feedtweetsv2 = []
    for (i,tweet) in enumerate(feedtweetsv1):
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
            filtered_feedtweetsv2.append(feedtweetsv2[i])
    return filtered_feedtweets,filtered_feedtweetsv2

os.chdir('/home/rockwell/Rockwell/backend/src/authorizer/hometimeline_data/')
hometimeline_files = sorted(glob.glob("*_home_*.json.gz"))
os.chdir('/home/rockwell/Rockwell/backend/src/authorizer/UserDatav2/')
hometimeline_files_v2 = sorted(glob.glob("*_home_*.json.gz"))

for i in range(len(hometimeline_files_v2)):
	with gzip.open('/home/rockwell/Rockwell/backend/src/authorizer/hometimeline_data/'+hometimeline_files[i],'r') as fin:
		data = json.load(fin)
		v1tweetobj = data['homeTweets']
		worker_id = data['worker_id']
		screenname = data['userObject']['screen_name']
	with gzip.open('/home/rockwell/Rockwell/backend/src/authorizer/UserDatav2/'+hometimeline_files_v2[i],'r') as fin:
		v2tweetobj = json.load(fin)
	feed_tweets,feed_tweets_v2 = filter_tweets(v1tweetobj,v2tweetobj["data"])
	db_tweet_payload = []
	for (i,tweet) in enumerate(feed_tweets):
		db_tweet = {'tweet_id':tweet["id"],'tweet_json':tweet, 'tweet_json_v2':feed_tweets_v2[i]}
		db_tweet_payload.append(db_tweet)
	feed_tweets_chronological = []
	feed_tweets_chronological_score = []
	for tweet in feed_tweets:
		feed_tweets_chronological.append(tweet)
		feed_tweets_chronological_score.append(-100)
	db_tweet_chronological_payload = []
	db_tweet_chronological_attn_payload = []
	rankk = 0
	for (i,tweet) in enumerate(feed_tweets_chronological):
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
			'predicted_score':feed_tweets_chronological_score[i]
		}
		db_tweet_chronological_payload.append(db_tweet)
		rankk = rankk + 1
	finalJson = []
	finalJson.append(db_tweet_payload)
	finalJson.append(db_tweet_chronological_payload)
	finalJson.append(db_tweet_chronological_attn_payload)
	finalJson.append(worker_id)
	finalJson.append(screenname)
	requests.post('http://127.0.0.1:5052/insert_timelines_attention_chronological',json=finalJson)
