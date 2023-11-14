#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 14:07:27 2023

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

proj_dir = "/home/saumya/Documents/Infodiversity/Rockwell/backend/src"
data_dir = "/home/saumya/Documents/Infodiversity/search_second_screen_data/"

tweet_fields = "attachments,author_id,conversation_id,created_at,entities,in_reply_to_user_id,lang,public_metrics,referenced_tweets,reply_settings"
user_fields = "id,name,username,created_at,description,entities,location,pinned_tweet_id,profile_image_url,protected,public_metrics,url,verified"
media_fields = "media_key,type,url,duration_ms,height,preview_image_url,public_metrics,width"
expansions = "author_id,referenced_tweets.id,attachments.media_keys"

search_url = "https://api.twitter.com/2/tweets/search/recent"

bearer_token = "AAAAAAAAAAAAAAAAAAAAAG1zMAEAAAAA3MKSCxkXn%2FB0dIZ3Zgq2dScBoZg%3DvFXgu6k3BOpWxc22eiuCFn7YETQck26gwSU20dhFHg5W2bYdiy"

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r

os.chdir(data_dir)

query_files = []
for fn in glob.glob("query_*.json.gz"):
    query_files.append(fn)

trustworthy_count = 0
untrustworthy_count = 0

trustworthy_done = False
untrustworthy_done = False

continue_to_loop_arr = [True] * len(query_files)
requests_remaining = 100

while(True):
    continue_to_loop = False
    for b in continue_to_loop_arr:
        continue_to_loop = continue_to_loop or b
    if not continue_to_loop:
        print("No more tweets left")
        print("Trustworthy collected : "+str(trustworthy_count))
        print("Untrustworthy collected : "+str(untrustworthy_count))
        break
    if trustworthy_done:
        if untrustworthy_done:
            print("Requeried number of tweets collected!!")
            break
    for (i,fn) in enumerate(query_files):
        if not continue_to_loop_arr[i]:
            continue
        print("Processing file : ")
        print(fn)
        with gzip.open(data_dir + fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            if data['next_token'] == '#DONE#':
                continue_to_loop_arr[i] = False
                continue
            if data['NG_rank'] == 'T':
                if trustworthy_count > 400:
                    print("TRUSTWORTHY DONE")
                    trustworthy_done = True
                    continue
            if data['NG_rank'] == 'NT':
                if untrustworthy_count > 400:
                    print("UNTRUSTWORTHY DONE")
                    untrustworthy_done = True
                    continue
            query_params = {'query':data['query'], 
                            'tweet.fields': tweet_fields, 
                            'user.fields': user_fields, 
                            'media.fields': media_fields, 
                            'expansions':expansions, 
                            'max_results':10}
            if data['next_token'] != 'NA':
                query_params['pagination_token'] = data['next_token']
            response = requests.get(search_url, auth=bearer_oauth, params=query_params)
            if 'meta' in response.json().keys():
                if 'result_count' in response.json()['meta'].keys():
                    if response.json()['meta']['result_count'] > 0:
                        if data['NG_rank'] == 'T':
                            trustworthy_count = trustworthy_count + response.json()['meta']['result_count']
                        else:
                            untrustworthy_count = untrustworthy_count + response.json()['meta']['result_count']
                        dataa = data['data'].copy()
                        dataa.append(response.json())
                        new_newest_id = response.json()['meta']['newest_id']
                        old_oldest_id = data['oldest_id']
                        if old_oldest_id == 0:
                            new_oldest_id = response.json()['meta']['oldest_id']
                        else:
                            new_oldest_id = old_oldest_id
                        new_count = data['count'] + response.json()['meta']['result_count']
                        if 'next_token' in response.json()['meta'].keys():
                            new_next_token = response.json()['meta']['next_token']
                        else:
                            new_next_token = "#DONE#"
                        writeObj = {
                                "query" : data['query'],
                                "newest_id" : new_newest_id,
                                "oldest_id" : new_oldest_id,
                                "count" : new_count,
                                "next_token" : new_next_token,
                                "NG_rank" : data['NG_rank'],
                                "data" : dataa,
                                "error" : "NA"
                            }
                        with gzip.open(data_dir + fn,'w') as outfile:
                            outfile.write(json.dumps(writeObj).encode('utf-8'))
                    else:
                        continue_to_loop_arr[i] = False
                else:
                    writeObj = {
                            "query" : data['query'],
                            "newest_id" : data['newest_id'],
                            "oldest_id" : data['oldest_id'],
                            "count" : data['count'],
                            "next_token" : data['next_token'],
                            "NG_rank" : data['NG_rank'],
                            "data" : data['data'],
                            "error" : response.json()
                        }
                    with gzip.open(data_dir + fn,'w') as outfile:
                        outfile.write(json.dumps(writeObj).encode('utf-8'))
                    continue_to_loop_arr[i] = False
            else:
                writeObj = {
                        "query" : data['query'],
                        "newest_id" : data['newest_id'],
                        "oldest_id" : data['oldest_id'],
                        "count" : data['count'],
                        "next_token" : data['next_token'],
                        "NG_rank" : data['NG_rank'],
                        "data" : data['data'],
                        "error" : response.json()
                    }
                with gzip.open(data_dir + fn,'w') as outfile:
                    outfile.write(json.dumps(writeObj).encode('utf-8'))
                continue_to_loop_arr[i] = False
            requests_remaining = int(response.headers['x-rate-limit-remaining'])
            if requests_remaining == 0:
                print("Sleeping for 18 mins!!!")
                time.sleep(1080)