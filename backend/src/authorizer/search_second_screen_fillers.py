#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 13:00:08 2023

@author: saumya
"""

import os
import re
import json
import time
import gzip
import glob
import numpy as np
import pandas as pd
import requests
from configparser import ConfigParser

data_dir = "/home/saumya/Documents/Infodiversity/search_second_screen_fillers/"

tweet_fields = "attachments,author_id,conversation_id,created_at,entities,in_reply_to_user_id,lang,public_metrics,referenced_tweets,reply_settings"
user_fields = "id,name,username,created_at,description,entities,location,pinned_tweet_id,profile_image_url,protected,public_metrics,url,verified"
media_fields = "media_key,type,url,duration_ms,height,preview_image_url,public_metrics,width"
expansions = "author_id,referenced_tweets.id,attachments.media_keys"

search_url = "https://api.twitter.com/2/tweets/search/recent"

bearer_token = "INSERT_BEARER_TOKEN"

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r

celeb = ['chrisbrown','justinbieber','iamcardib','Beyonce','Adele',
         'KingJames','StephenCurry30','TomBrady','TigerWoods','Simone_Biles',
         'RobertDowneyJr','Trevornoah','DaveChapelleETH','KevinHart4real',
         'KimKardashian','taylorswift13','IAmSteveHarvey','LewisHamilton','MarcusRashford','MKBHD']

next_tokens = ["NA"]*len(celeb)

tweets = []
for i in range(len(celeb)):
    tweets.append({})

num_tweets = 0

for i in range(len(celeb)):
    print(i)
    if num_tweets > 200:
        print("All tweets collected")
        break
    celeb_now = celeb[i]
    query_params = {'query':'from:'+celeb_now, 
                    'tweet.fields': tweet_fields, 
                    'user.fields': user_fields, 
                    'media.fields': media_fields, 
                    'expansions':expansions, 
                    'max_results':10}
    response = requests.get(search_url, auth=bearer_oauth, params=query_params)
    if 'meta' in response.json().keys():
        if 'result_count' in response.json()['meta'].keys():
            if response.json()['meta']['result_count'] > 0:
                num_tweets = num_tweets + response.json()['meta']['result_count']
                tweets[i] = response.json()
                if 'next_token' in response.json()['meta'].keys():
                    next_tokens[i] = response.json()['meta']['next_token']
                else:
                    next_tokens[i] = "#DONE#"
            else:
                next_tokens[i] = "#DONE#"
        else:
            print("PROBLEM!!!")
            print(celeb_now)
            print(response)
    else:
        print("PROBLEM!!!")
        print(celeb_now)
        print(response)
    requests_remaining = int(response.headers['x-rate-limit-remaining'])
    if requests_remaining == 0:
        print("Sleeping for 18 mins!!!")
        time.sleep(1080)

tweets_2 = []
for i in range(len(celeb)):
    tweets_2.append({})

for i in range(len(celeb)):
    print(i)
    if num_tweets > 200:
        print("All tweets collected")
        break
    if next_tokens[i] == "#DONE#":
        continue
    celeb_now = celeb[i]
    query_params = {'query':'from:'+celeb_now, 
                    'tweet.fields': tweet_fields, 
                    'user.fields': user_fields, 
                    'media.fields': media_fields, 
                    'expansions':expansions, 
                    'max_results':25,
                    'pagination_token':next_tokens[i]}
    response = requests.get(search_url, auth=bearer_oauth, params=query_params)
    if 'meta' in response.json().keys():
        if 'result_count' in response.json()['meta'].keys():
            if response.json()['meta']['result_count'] > 0:
                num_tweets = num_tweets + response.json()['meta']['result_count']
                tweets_2[i] = response.json()
                if 'next_token' in response.json()['meta'].keys():
                    next_tokens[i] = response.json()['meta']['next_token']
                else:
                    next_tokens[i] = "#DONE#"
            else:
                next_tokens[i] = "#DONE#"
        else:
            print("PROBLEM!!!")
            print(celeb_now)
            print(response)
    else:
        print("PROBLEM!!!")
        print(celeb_now)
        print(response)
    requests_remaining = int(response.headers['x-rate-limit-remaining'])
    if requests_remaining == 0:
        print("Sleeping for 18 mins!!!")
        time.sleep(1080)

tweets_3 = []
for i in range(len(celeb)):
    tweets_3.append({})

for i in range(len(celeb)):
    print(i)
    if num_tweets > 200:
        print("All tweets collected")
        break
    if next_tokens[i] == "#DONE#":
        continue
    celeb_now = celeb[i]
    query_params = {'query':'from:'+celeb_now, 
                    'tweet.fields': tweet_fields, 
                    'user.fields': user_fields, 
                    'media.fields': media_fields, 
                    'expansions':expansions, 
                    'max_results':10,
                    'pagination_token':next_tokens[i]}
    response = requests.get(search_url, auth=bearer_oauth, params=query_params)
    if 'meta' in response.json().keys():
        if 'result_count' in response.json()['meta'].keys():
            if response.json()['meta']['result_count'] > 0:
                num_tweets = num_tweets + response.json()['meta']['result_count']
                tweets_3[i] = response.json()
                if 'next_token' in response.json()['meta'].keys():
                    next_tokens[i] = response.json()['meta']['next_token']
                else:
                    next_tokens[i] = "#DONE#"
            else:
                next_tokens[i] = "#DONE#"
        else:
            print("PROBLEM!!!")
            print(celeb_now)
            print(response)
    else:
        print("PROBLEM!!!")
        print(celeb_now)
        print(response)
    requests_remaining = int(response.headers['x-rate-limit-remaining'])
    if requests_remaining == 0:
        print("Sleeping for 18 mins!!!")
        time.sleep(1080)

for i in range(len(celeb)):
    all_tweets = []
    if tweets[i]:
        all_tweets.append(tweets[i])
    if tweets_2[i]:
        all_tweets.append(tweets_2[i])
    if tweets_3[i]:
        all_tweets.append(tweets_3[i])
    if all_tweets:
        writeObj = {"screenname":celeb[i],"tweets":all_tweets}
        with gzip.open("/home/saumya/Documents/Infodiversity/search_second_screen_fillers/celeb_{}.json.gz".format(i),'w') as outfile:
            outfile.write(json.dumps(writeObj).encode('utf-8'))
