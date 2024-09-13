#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 14:12:02 2023

@author: saumya
"""

import re
import os
import glob
import gzip
import requests
import threading
import pandas as pd
import math
import json
import joblib
import datetime
import surprise
from dateutil import parser
from collections import Counter
from multiprocessing import Manager
from multiprocessing.dummy import Pool

data_dir = "/home/saumya/Documents/Infodiversity/search_second_screen_data/"
data_dir_celebs = "/home/saumya/Documents/Infodiversity/search_second_screen_fillers/"
proj_dir = "/home/saumya/Documents/Infodiversity/Rockwell/backend/src"

timeline_params = {
    "tweet.fields" : "id,text,edit_history_tweet_ids,attachments,author_id,conversation_id,created_at,entities,in_reply_to_user_id,lang,public_metrics,referenced_tweets,reply_settings",
    "user.fields" : "id,name,username,created_at,description,entities,location,pinned_tweet_id,profile_image_url,protected,public_metrics,url,verified",
    "media.fields": "media_key,type,url,duration_ms,height,preview_image_url,public_metrics,width",
    "expansions" : "author_id,referenced_tweets.id,attachments.media_keys"
}

bearer_token = "AAAAAAAAAAAAAAAAAAAAAG1zMAEAAAAA3MKSCxkXn%2FB0dIZ3Zgq2dScBoZg%3DvFXgu6k3BOpWxc22eiuCFn7YETQck26gwSU20dhFHg5W2bYdiy"

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r

def createlookups(v2tweetobj,includenext=True,onlyincludequote=False):
    tweet_lookup = {}
    media_lookup = {}
    user_lookup = {}
    next_level_ids = []

    if "data" in v2tweetobj.keys():
        for v2tweet in v2tweetobj["data"]:
            tweet_lookup[v2tweet["id"]] = v2tweet
            if includenext:
                if "referenced_tweets" in v2tweet.keys():
                    for referenced_tweet in v2tweet["referenced_tweets"]:
                        if referenced_tweet["type"] != "replied_to":
                            if onlyincludequote:
                                if referenced_tweet["type"] == "quoted":
                                    next_level_ids.append(referenced_tweet["id"])
                            else:
                                next_level_ids.append(referenced_tweet["id"])

    if "includes" in v2tweetobj.keys():
        if "media" in v2tweetobj["includes"].keys():
            for media_ele in v2tweetobj["includes"]["media"]:
                media_lookup[media_ele["media_key"]] = media_ele
        if "users" in v2tweetobj["includes"].keys():
            for user_ele in v2tweetobj["includes"]["users"]:
                user_lookup[user_ele["id"]] = user_ele

    return tweet_lookup,media_lookup,user_lookup,next_level_ids

def addallfields(v2tweet,v2user,v2media,v2tweetobj_user=None,v2tweetobj_fav=None):
    v1tweet = {}
    v1tweet["id"] = v2tweet["id"]
    v1tweet["id_str"] = v2tweet["id"]
    v1tweet["full_text"] = v2tweet["text"]
    v1tweet["favorite_count"] = v2tweet["public_metrics"]["like_count"]
    v1tweet["retweet_count"] = v2tweet["public_metrics"]["retweet_count"]
    v1tweet["created_at"] = v2tweet["created_at"]
    v1tweet["in_reply_to_status_id_str"] = ""
    v1tweet["favorited"] = False
    v1tweet["retweeted"] = False

    if "referenced_tweets" in v2tweet.keys():
        for referenced_tweet in v2tweet["referenced_tweets"]:
            if referenced_tweet["type"] == "replied_to":
                v1tweet["in_reply_to_status_id_str"] = referenced_tweet["id"]

    if v2tweetobj_user:
        if "data" in v2tweetobj_user.keys():
            for v2tweet_user in v2tweetobj_user["data"]:
                if "referenced_tweets" in v2tweet_user.keys():
                    for referenced_tweet in v2tweet_user["referenced_tweets"]:
                        if referenced_tweet["type"] == "retweeted":
                            if referenced_tweet["id"] == v2tweet["id"]:
                                v1tweet["retweeted"] = True

    if v2tweetobj_fav:
        if "data" in v2tweetobj_fav.keys():
            for v2tweet_fav in v2tweetobj_fav["data"]:
                if v2tweet_fav["id"] == v2tweet["id"]:
                    v1tweet["favorited"] = True
    
    v1tweet["user"] = {}
    v1tweet["user"]["name"] = v2user[v2tweet["author_id"]]["name"]
    v1tweet["user"]["profile_image_url"] = v2user[v2tweet["author_id"]]["profile_image_url"]
    v1tweet["user"]["screen_name"] = v2user[v2tweet["author_id"]]["username"]
    v1tweet["user"]["url"] = ""
    if "url" in v2user[v2tweet["author_id"]].keys():
        v1tweet["user"]["url"] = v2user[v2tweet["author_id"]]["url"]
    
    if "entities" in v2tweet.keys():
        if "urls" in v2tweet["entities"]:
            v1tweet["entities"] = {}
            v1tweet["entities"]["urls"] = []
            for v2_url in v2tweet["entities"]["urls"]:
                v1_url = {}
                v1_url["indices"] = [v2_url["start"],v2_url["end"]]
                v1_url["display_url"] = v2_url["display_url"]
                v1_url["expanded_url"] = v2_url["expanded_url"]
                v1_url["url"] = v2_url["url"]
                v1tweet["entities"]["urls"].append(v1_url)
    
    if "attachments" in v2tweet.keys():
        if "media_keys" in v2tweet["attachments"].keys():
            if "entities" not in v1tweet.keys():
                v1tweet["entities"] = {}
            v1tweet["entities"]["media"] = []
            for media_key in v2tweet["attachments"]["media_keys"]:
                v1_media = {}
                if "url" in v2media[media_key].keys():
                    v1_media["media_url"] = v2media[media_key]["url"]
                    v1_media["expanded_url"] = v2media[media_key]["url"]
                else:
                    v1_media["media_url"] = v2media[media_key]["preview_image_url"]
                    v1_media["expanded_url"] = v2media[media_key]["preview_image_url"]
                v1tweet["entities"]["media"].append(v1_media)
    
    return v1tweet

def convertv2tov1(v2tweetobj,v2tweetobj_user=None,v2tweetobj_fav=None):

    v1_tweets_all = []

    tweet_1_lookup = {}
    tweet_1_media_lookup = {}
    tweet_1_user_lookup = {}

    tweet_2_lookup = {}
    tweet_2_media_lookup = {}
    tweet_2_user_lookup = {}

    tweet_3_lookup = {}
    tweet_3_media_lookup = {}
    tweet_3_user_lookup = {}

    tweet_2_ids = []
    tweet_3_ids = []

    tweet_1_lookup,tweet_1_media_lookup,tweet_1_user_lookup,tweet_2_ids = createlookups(v2tweetobj)

    if tweet_2_ids:
        new_tweet_params = {
            "ids" : ",".join(tweet_2_ids),
            "tweet.fields" : timeline_params["tweet.fields"],
            "user.fields" : timeline_params["user.fields"],
            "media.fields" : timeline_params["media.fields"],
            "expansions" : timeline_params["expansions"],
        }
        response_tweet_2 = requests.get("https://api.twitter.com/2/tweets", params=new_tweet_params,auth=bearer_oauth)
        v2tweetobj_2 = json.loads(response_tweet_2.text)
        tweet_2_lookup,tweet_2_media_lookup,tweet_2_user_lookup,tweet_3_ids = createlookups(v2tweetobj_2,onlyincludequote=True)
    
    if tweet_3_ids:
        new_tweet_params = {
            "ids" : ",".join(tweet_3_ids),
            "tweet.fields" : timeline_params["tweet.fields"],
            "user.fields" : timeline_params["user.fields"],
            "media.fields" : timeline_params["media.fields"],
            "expansions" : timeline_params["expansions"],
        }
        response_tweet_3 = requests.get("https://api.twitter.com/2/tweets", params=new_tweet_params, auth=bearer_oauth)
        v2tweetobj_3 = json.loads(response_tweet_3.text)
        tweet_3_lookup,tweet_3_media_lookup,tweet_3_user_lookup,no_matter_ids = createlookups(v2tweetobj_3,includenext=False)
    
    if "data" in v2tweetobj.keys():
        for v2tweet in v2tweetobj["data"]:
            v1tweet = addallfields(v2tweet,tweet_1_user_lookup,tweet_1_media_lookup,v2tweetobj_user=v2tweetobj_user,v2tweetobj_fav=v2tweetobj_fav)
            if "referenced_tweets" in v2tweet.keys():
                for referenced_tweet in v2tweet["referenced_tweets"]:
                    if referenced_tweet["type"] == "retweeted":
                        if referenced_tweet["id"] in tweet_2_lookup.keys():
                            v2tweet_retweeted = tweet_2_lookup[referenced_tweet["id"]]
                            v1tweet["retweeted_status"] = addallfields(v2tweet_retweeted,tweet_2_user_lookup,tweet_2_media_lookup)
                            if "referenced_tweets" in v2tweet_retweeted.keys():
                                for double_referenced_tweet in v2tweet_retweeted["referenced_tweets"]:
                                    if double_referenced_tweet["type"] == "quoted":
                                        if double_referenced_tweet["id"] in tweet_3_lookup.keys():
                                            v2tweet_retweeted_quoted = tweet_3_lookup[double_referenced_tweet["id"]]
                                            v1tweet["retweeted_status"]["quoted_status"] = addallfields(v2tweet_retweeted_quoted,tweet_3_user_lookup,tweet_3_media_lookup)
                    if referenced_tweet["type"] == "quoted":
                        if referenced_tweet["id"] in tweet_2_lookup.keys():
                            v2tweet_quoted = tweet_2_lookup[referenced_tweet["id"]]
                            v1tweet["quoted_status"] = addallfields(v2tweet_quoted,tweet_2_user_lookup,tweet_2_media_lookup)
            v1_tweets_all.append(v1tweet)
    
    return v1_tweets_all

def gettwitterhandle(url):
    try:
        return url.split("/")[3]
    except:
        return ""

def addtwitterNG(df):
    return (df.assign(twitter=df.twitter.apply(gettwitterhandle)))

def extractfromentities(payload):
    urls_extracted = []
    if "entities" in payload:
        entities = payload["entities"]
        for url_obj in entities["urls"]:
            urls_extracted.append(url_obj["expanded_url"])
        if "media" in entities:
            for media_obj in payload["entities"]["media"]:
                urls_extracted.append(media_obj["expanded_url"])
    if "extended_entities" in payload:
        for media_obj in payload["extended_entities"]["media"]:
            urls_extracted.append(media_obj["expanded_url"])
    return list(set(urls_extracted))

# by default cache results in memory
_CACHE = {}

def _newcache(fn=None):
    if fn is None:
        return dict()
    else:
        try:
            import dbhash
            return dbhash.open(fn, 'w')
        except ImportError:
            import sys
            print("warning: cannot import BerkeleyDB (dbhash), "
                  "storing cache in memory.",
                  file=sys.stderr)
            return dict()

def _setcache(fn=None):
    global _CACHE
    _CACHE = _newcache(fn)

def init(queue):
    global idx
    idx = queue.get()

def unshortenone(urlidx):
    global idx
    if urlidx[0] % 100 == 0:
        print(urlidx[0])
    u = urlidx[1]
    uk = u.encode('utf-8')
    if uk in _CACHE:
        return _CACHE[uk]
    try:
        r = requests.head(u, allow_redirects=True,timeout=10)
        _CACHE[uk] = r.url
        return r.url
    except requests.exceptions.RequestException:
        return u

def unshorten(urls, threads=None, cachepath=None):
    """
    Iterator over unshortened versions of input URLs. Follows redirects using
    HEAD commands. Operates in parallel using multiple threads of execution.

    Parameters
    ==========

    urls : iterator
        a sequence of short URLs.

    threads : int
        optional; number of threads to use.

    cachepath : str
        optional; path to file with cache (for reuse). By default will use
        in-memory cache.
    """
    _setcache(cachepath)

    d = threading.local()
    def set_num(counter):
        d.id = next(counter) + 1

    ids = list(range(threads))
    manager = Manager()
    idQueue = manager.Queue()

    for i in ids:
        idQueue.put(i)

    pool = Pool(threads,init,(idQueue,))
    urlswithidx = [list(uidx) for uidx in zip(range(len(urls)),urls)]
    for url in pool.imap(unshortenone, urlswithidx):
        yield url

def integrate_NG_iffy(ng_fn,iffyfile):
    iffy_domains = pd.read_csv(iffyfile)['Domain'].values.tolist()
    with open(ng_fn) as f:
        obj = json.load(f)
        
    d = {
        "identifier": [elem["identifier"] for elem in filter(None, obj) if re.match("en", elem["locale"])],
        "rank": [elem["rank"] for elem in filter(None, obj) if re.match("en", elem["locale"])],
        "score": [elem["score"] for elem in filter(None, obj) if re.match("en", elem["locale"])],
        "twitter": [elem['metadata'].get("TWITTER", {"body": ""})["body"] for elem in filter(None, obj) if re.match("en", elem["locale"])]
    }
    
    ng_domains = pd.DataFrame(d)
    ng_domains = addtwitterNG(ng_domains)
    ng_domains = ng_domains.rename(columns={"identifier": "domain"})
    
    ng_domain_values = ng_domains['domain'].values
    
    for iffy_domain in iffy_domains:
        if iffy_domain not in ng_domain_values:
            df_iffy = {'domain':iffy_domain,'rank':'N','score':-100,'twitter':'NA'}
            ng_domains = ng_domains.append(df_iffy,ignore_index=True)

    return ng_domains

def unshorten_and_tag_NG(all_urls,ng_domains):
    ng_domain_values = ng_domains.loc[ng_domains['rank'].isin(['T','N'])]['domain'].unique()
    ng_twitter_values = ng_domains.loc[ng_domains['rank'].isin(['T','N'])]['twitter'].unique()
    #urls_unshorted = all_urls.copy()
    urls_unshorted = []
    outputs = unshorten(all_urls, threads=20, cachepath='/home/saumya/')
    for url in outputs:
        urls_unshorted.append(url)
    
    urls_domains = []
    urls_twitter = []
    for url in urls_unshorted:
        domain = ".".join(url.split("/")[2].split(".")[-2:])
        urls_domains.append(domain)
        if domain == "twitter.com":
            try:
                urls_twitter.append(url.split("/")[3])
            except:
                urls_twitter.append("NA")
        else:
            urls_twitter.append("NA")
    
    urls_tagged = []
    for idx in range(len(urls_domains)):
        if urls_domains[idx] in ng_domain_values:
            urls_tagged.append(urls_domains[idx])
        elif urls_twitter[idx] != "NA":
            if urls_twitter[idx] in ng_twitter_values: 
                try:
                    twitter_domain = ng_domains.loc[(ng_domains['twitter'] == urls_twitter[idx])]['domain'][0]
                    urls_tagged.append(twitter_domain)
                except KeyError:
                    urls_tagged.append("NA")
                    continue
            else:
                urls_tagged.append("NA")
        else:
            urls_tagged.append("NA")
    return urls_tagged

def tag_NG_handles(all_handles,ng_domains):
    ng_twitter_values = ng_domains.loc[ng_domains['rank'].isin(['T','N'])]['twitter'].unique()
    handles_tagged = []
    for handle in all_handles:
        if handle in ng_twitter_values:
            corrs_domain = ng_domains.loc[(ng_domains['twitter'] == handle)]['domain'].values.tolist()
            actual_domain = 'NA'
            for dd in corrs_domain:
                if dd.count('.') == 1:
                    actual_domain = dd
                    break
            if actual_domain == 'NA':
                actual_domain = corrs_domain[0]
            handles_tagged.append(actual_domain)
        else:
            handles_tagged.append("NA")
    return handles_tagged

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

os.chdir(data_dir)

query_files = []
for fn in glob.glob("query_*.json.gz"):
    query_files.append(fn)

insert_tweet = []

for (i,fn) in enumerate(query_files):
    with gzip.open(data_dir + fn, 'r') as fin:
        data = json.loads(fin.read().decode('utf-8'))
        if data['data']:
            v1tweetobj_arr = []
            for tweet_data in data['data']:
                v1tweetobj = convertv2tov1(tweet_data)
                feed_tweets,feed_tweets_v2 = filter_tweets(v1tweetobj,tweet_data['data'])
                for (i,tweet) in enumerate(feed_tweets):
                    obj = {
                        'tweet_id':tweet['id'],
                        'tweet_json':tweet,
                        'tweet_json_v2':feed_tweets_v2[i],
                        'ng_sources':"NA",
                        'ng_rank':"NA",
                        'ng_score':-1000,
                        'location':"NA"
                    }
                    insert_tweet.append(obj)

os.chdir(data_dir_celebs)

celeb_files = []
for fn in glob.glob("celeb_*.json.gz"):
    celeb_files.append(fn)

for (i,fn) in enumerate(celeb_files[2:len(celeb_files)]):
    with gzip.open(data_dir_celebs + fn, 'r') as fin:
        data = json.loads(fin.read().decode('utf-8'))
        if data['tweets']:
            v1tweetobj_arr = []
            for tweet_data in data['tweets']:
                v1tweetobj = convertv2tov1(tweet_data)
                feed_tweets,feed_tweets_v2 = filter_tweets(v1tweetobj,tweet_data['data'])
                for (i,tweet) in enumerate(feed_tweets):
                    obj = {
                        'tweet_id':tweet['id'],
                        'tweet_json':tweet,
                        'tweet_json_v2':feed_tweets_v2[i],
                        'ng_sources':"NA",
                        'ng_rank':"NA",
                        'ng_score':-1000,
                        'location':"NA"
                    }
                    insert_tweet.append(obj)