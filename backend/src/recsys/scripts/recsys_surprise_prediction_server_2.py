#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 10:51:27 2023

@author: saumya
"""

import re
import math
import glob
import gzip
import json
import requests
import joblib
import random
import numpy as np
import pandas as pd
from itertools import groupby
from flask import Flask, render_template, request, url_for, jsonify
import threading
import surprise
from collections import Counter
from multiprocessing import Manager
from multiprocessing.dummy import Pool

app = Flask(__name__)

app.debug = False

trainset = None
algo = None

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

def unshorten_and_tag_NG(all_urls,ng_domains,training_ng_domains):
    ng_domain_values = ng_domains['domain'].unique()
    ng_twitter_values = ng_domains['twitter'].unique()
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
            if urls_domains[idx] in training_ng_domains:
                urls_tagged.append(urls_domains[idx])
            else:
                urls_tagged.append("NA")
        elif urls_twitter[idx] != "NA":
            if urls_twitter[idx] in ng_twitter_values: 
                try:
                    twitter_domain = ng_domains.loc[(ng_domains['twitter'] == urls_twitter[idx])]['domain'][0]
                    if twitter_domain in training_ng_domains:
                        urls_tagged.append(twitter_domain)
                    else:
                        urls_tagged.append("NA")
                except KeyError:
                    urls_tagged.append("NA")
                    continue
            else:
                urls_tagged.append("NA")
        else:
            urls_tagged.append("NA")
    return urls_tagged

def pageArrangement(ng_tweets, ng_tweets_ratings, non_ng_tweets):
    ranked_ng_tweets = []
    final_resultant_feed = []
    resultant_feed = [None] * 50
    pt = len(ng_tweets) / (len(non_ng_tweets) + len(non_ng_tweets))

    #We do not want more than 50% NewsGuard tweets on the feed
    if pt > 0.5:
        pt = 0.5

    #Rank the NG tweets
    for i in range(len(ng_tweets)):
        ranked_ng_tweets.append((ng_tweets[i], ng_tweets_ratings[i]))
    
    #Top 50 tweets from NewsGuard
    ranked_ng_tweets.sort(key=lambda a: a[1], reverse=True)
    selection_threshold_rnk = 50 * pt
    top_50 = [None] * math.ceil(selection_threshold_rnk) #ranked_ng_tweets[0:selection_threshold_rnk]
    for i in range(len(top_50)):
        top_50[i] = ranked_ng_tweets[i]

    #50 other tweets
    selection_threshold = 50 * (1 - pt)
    other_tweets = non_ng_tweets[0:math.floor(selection_threshold)]

    #Assign positions in feed to the NG and non NG tweets
    for i in range(len(resultant_feed)):
        chance = random.randint(1, 100)
        if chance < (pt * 100) and len(top_50) != 0:
            resultant_feed[i] = top_50[0][0]
            top_50.pop(0)
        else:
            if len(other_tweets) != 0:
                resultant_feed[i] = other_tweets[0]
                other_tweets.pop(0)

    for tweet in resultant_feed:
        if tweet != None:
            final_resultant_feed.append(tweet)

    #print("Res Feed Len: " + str(len(final_resultant_feed)))
    return final_resultant_feed

@app.route('/recsys_rerank', methods=['GET'])
def recsys_rerank():
	payload = request.json
	hometimeline = payload[0]
	screen_name = payload[1]

	hometimeline_urls = []
	hometimeline_tweets = {}

	for tweet in hometimeline:
		tweet_id = tweet["id_str"]
		hometimeline_tweets[tweet_id] = tweet
		if 'retweeted_status' in tweet:
			urls_extracted = extractfromentities(tweet['retweeted_status'])
			for url in urls_extracted:
				hometimeline_urls.append({"tweet_id": tweet_id,"url":url})
			if 'quoted_status' in tweet['retweeted_status']:
				urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
				for url in urls_extracted:
					hometimeline_urls.append({"tweet_id": tweet_id,"url":url})
		else:
			if 'quoted_status' in tweet:
				urls_extracted = extractfromentities(tweet['quoted_status'])
				for url in urls_extracted:
					hometimeline_urls.append({"tweet_id": tweet_id,"url":url})
			urls_extracted = extractfromentities(tweet)
			for url in urls_extracted:
				hometimeline_urls.append({"tweet_id": tweet_id,"url":url})

	pd_hometimeline_urls = pd.DataFrame(hometimeline_urls)
	all_urls = pd_hometimeline_urls['url'].values.tolist()
	hometimeline_urls_tagged = unshorten_and_tag_NG(all_urls,ng_domains,training_ng_domains)
	pd_hometimeline_urls = pd.concat([pd_hometimeline_urls,pd.DataFrame(hometimeline_urls_tagged,columns=['tagged_urls'])],axis=1)

	inner_uid = trainset.to_inner_uid(screen_name)

	predicted_rating = {}
	for index,row in pd_hometimeline_urls.iterrows():
		if row['tagged_urls'] != 'NA':
			try:
				predicted_rating[row['tweet_id']] = algo.predict(uid=screen_name, iid=row['tagged_urls']).est
			except ValueError:
				continue

	predicted_rating_tweets = predicted_rating.keys()
	NG_tweets = []
	NG_tweets_ratings = []
	non_NG_tweets = []

	for tweet_id in hometimeline_tweets.keys():
		if tweet_id in predicted_rating_tweets:
			NG_tweets.append(hometimeline_tweets[tweet_id])
			NG_tweets_ratings.append(predicted_rating[tweet_id])
		else:
			non_NG_tweets.append(hometimeline_tweets[tweet_id])

	final_resultant_feed = pageArrangement(NG_tweets,NG_tweets_ratings,non_NG_tweets)

	return jsonify(data=final_resultant_feed)

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
	print("Reading NewsGuard, Iffy and training domains")
	ng_fn = "../NewsGuardIffy/label-2022101916.json"
	iffyfile = "../NewsGuardIffy/iffy.csv"
	training_ng_domains_file = '../data/hoaxy_dataset_training_domains_2.csv'
	ng_domains = integrate_NG_iffy(ng_fn,iffyfile)
	training_ng_domains = pd.read_csv(training_ng_domains_file)['Domains'].values.tolist()

	print("Preparing Training set")
	hoaxy_training_file = '../data/hoaxy_dataset_training_2.csv'
	pd_hoaxy_training_dataset = pd.read_csv(hoaxy_training_file)
	pd_hoaxy_training_dataset = pd_hoaxy_training_dataset.drop(columns=['Unnamed: 0'])
	reader = surprise.reader.Reader(rating_scale=(0, 1))
	training_data = surprise.dataset.Dataset.load_from_df(pd_hoaxy_training_dataset, reader) 
	trainset = training_data.build_full_trainset()

	print("Preparing model")
	model_file = '../model/hoaxy_recsys_model_2.sav'
	algo = joblib.load(model_file)

	app.run(host = "0.0.0.0", port = 5054)