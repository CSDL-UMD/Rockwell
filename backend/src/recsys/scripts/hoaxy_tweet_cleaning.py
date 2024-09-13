#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 18:44:36 2023

@author: saumya
"""

import os
import json
import glob
import pandas as pd

data_dir = "/home/saumya/hoaxy_tweets/"
os.chdir(data_dir)

tweet_files = []
for fn in glob.glob("tweets_*.json"):
    tweet_files.append(fn)

users_handle = []
handle_items = []
users_urls = []
url_items = []

for filee in tweet_files:
    print(filee)
    with open(filee,'r') as fin:
        dataa = json.load(fin)
    for data in dataa['data_hoaxy']:
        author_id = data['data']['author_id'].strip()
        for user in data['includes']['users']:
            user_id = user['id'].strip()
            if user_id != author_id:
                users_handle.append(author_id)
                handle_items.append(user_id)
        if 'tweets' in data['includes']:
            for tweet in data['includes']['tweets']:
                if 'entities' in tweet.keys():
                    if 'urls' in tweet['entities'].keys():
                        for url in tweet['entities']['urls']:
                            users_urls.append(author_id)
                            url_items.append(url['expanded_url'])

pd_combine_handle = pd.concat([pd.DataFrame(users_handle,columns=['Users']),pd.DataFrame(handle_items,columns=['Handles'])],axis=1)
pd_combine_url = pd.concat([pd.DataFrame(users_urls,columns=['Users']),pd.DataFrame(url_items,columns=['URLS'])],axis=1)

pd_combine_handle.to_csv('/home/saumya/hoaxy_handles.csv')
pd_combine_url.to_csv('/home/saumya/hoaxy_URLS.csv')