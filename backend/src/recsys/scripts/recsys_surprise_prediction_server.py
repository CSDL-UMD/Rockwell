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
from urllib.parse import urlsplit
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

TTL_DNS_CACHE=300  # Time-to-live of DNS cache
MAX_TCP_CONN=50  # Throttle at max these many simultaneous connections
TIMEOUT_TOTAL=10  # Each request times out after these many seconds

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

async def unshortenone(url, session, pattern=None, maxlen=None, 
                       cache=None, timeout=None):
    # If user specified list of domains, check netloc is in it, otherwise set
    # to False (equivalent of saying there is always a match against the empty list)
    if pattern is not None:
        domain = urlsplit(url).netloc
        match = re.search(pattern, domain)
        no_match = (match is None)
    else:
        no_match = False
    # If user specified max URL length, check length, otherwise set to False
    # (equivalent to setting max length to infinity -- any length is OK)
    too_long = (maxlen is not None and len(url) > maxlen)
    # Ignore if either of the two exclusion criteria applies.
    if too_long or no_match:
        return url
    if cache is not None and url in cache:
        return str(cache[url])
    else:
        try:
            # await asyncio.sleep(0.01)
            resp = await session.head(url, timeout=timeout, 
                                      ssl=False, allow_redirects=True)
            expanded_url = str(resp.url)
            if url != expanded_url:
                if cache is not None and url not in cache:
                    # update cache if needed
                    cache[url] = expanded_url
            return expanded_url
        except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeError):
            return url


# Thanks: https://blog.jonlu.ca/posts/async-python-http
async def gather_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)
    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def _unshorten(*urls, cache=None, domains=None, maxlen=None):
    if domains is not None:
        pattern = re.compile(f"({'|'.join(domains)})", re.I)
    else:
        pattern = None
    conn = aiohttp.TCPConnector(ttl_dns_cache=TTL_DNS_CACHE, limit=None)
    u1 = unshortenone
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_TOTAL)
    async with aiohttp.ClientSession(connector=conn) as session:
        return await gather_with_concurrency(MAX_TCP_CONN, 
                                             *(u1(u, session, cache=cache,
                                                  maxlen=maxlen,
                                                  pattern=pattern, 
                                                  timeout=timeout) for u in urls))


def unshorten(*args, **kwargs):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop = asyncio.get_event_loop()
    return loop.run_until_complete(_unshorten(*args, **kwargs))

def unshorten_and_tag_NG(all_urls,ng_domains,training_ng_domains):
    ng_domain_values = ng_domains['domain'].unique()
    ng_twitter_values = ng_domains['twitter'].unique()
    urls_unshorted = []
    cache = {}
    shortening_domains = []
    with open('../data/shorturl-services-list.csv') as f:
        f.readline()
        shortening_domains = [line.strip(',\n') for line in f]
    maxlen = 30
    all_urls_star = (url for url in all_urls)
    outputs = unshorten(*all_urls_star, cache=cache, domains=shortening_domains, maxlen=maxlen)
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
	print("HERE!!!!")
	payload = request.json
	hometimeline = payload[0]
	usertimeline = payload[1]
	#favtimeline = payload[2]

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

	engaged_urls = []

	for tweet in usertimeline:
		tweet_id = tweet["id_str"]
		if 'retweeted_status' in tweet:
			urls_extracted = extractfromentities(tweet['retweeted_status'])
			for url in urls_extracted:
				engaged_urls.append(url)
			if 'quoted_status' in tweet['retweeted_status']:
				urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
				for url in urls_extracted:
					engaged_urls.append(url)
		else:
			if 'quoted_status' in tweet:
				urls_extracted = extractfromentities(tweet['quoted_status'])
				for url in urls_extracted:
					engaged_urls.append(url)
			urls_extracted = extractfromentities(tweet)
			for url in urls_extracted:
				engaged_urls.append(url)

	"""
	for tweet in favtimeline:
		tweet_id = tweet["id_str"]
		if 'retweeted_status' in tweet:
			urls_extracted = extractfromentities(tweet['retweeted_status'])
			for url in urls_extracted:
				engaged_urls.append(url)
			if 'quoted_status' in tweet['retweeted_status']:
				urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
				for url in urls_extracted:
					engaged_urls.append(url)
		else:
			if 'quoted_status' in tweet:
				urls_extracted = extractfromentities(tweet['quoted_status'])
				for url in urls_extracted:
					engaged_urls.append(url)
			urls_extracted = extractfromentities(tweet)
			for url in urls_extracted:
				engaged_urls.append(url)
	"""

	hometimeline_urls_length = len(pd_hometimeline_urls)

	all_urls = pd_hometimeline_urls['url'].values.tolist() + engaged_urls

	all_urls_tagged = unshorten_and_tag_NG(all_urls,ng_domains,training_ng_domains)

	hometimeline_urls_tagged = all_urls_tagged[0:hometimeline_urls_length]
	engaged_urls_tagged = all_urls_tagged[hometimeline_urls_length:]

	pd_hometimeline_urls = pd.concat([pd_hometimeline_urls,pd.DataFrame(hometimeline_urls_tagged,columns=['tagged_urls'])],axis=1)

	domains = []
	ratings = []
	engaged_urls_tagged = [url for url in engaged_urls_tagged if url != 'NA']
	domain_counter = Counter(engaged_urls_tagged)
	for dd in domain_counter.keys():
	    tf = domain_counter[dd]/len(engaged_urls_tagged)
	    idf = domain_idf_dict[dd]
	    domains.append(dd)
	    ratings.append(tf/idf)
	"""
    total = len(engaged_urls_tagged)
	if total == 0:
		for dd in training_ng_domains:
			domains.append(dd)
			ratings.append(0.000005)
	if total == 1:
	    domains.append(engaged_urls_tagged[0])
	    ratings.append(1.0)
	else:
	    total_log = math.log10(total)
	    domain_counter = Counter(engaged_urls_tagged)
	    for dd in domain_counter.keys():
	        fracc = 0.1
	        if domain_counter[dd] > 1:
	            fracc = math.log10(domain_counter[dd])
	            rating_log = float(fracc)/float(total_log)
	            domains.append(dd)
	            ratings.append(rating_log)
	        else:
	            domains.append(dd)
	            ratings.append(0.005)
    """

	item_latent = algo.qi
	item_latent_transpose = np.matrix.transpose(item_latent)
	vector_len = item_latent.shape[0]

	user_vector = np.zeros(vector_len)
	for idx in range(len(domains)):
	    domain = domains[idx]
	    rating = ratings[idx]
	    try:
	        inner_iid = trainset.to_inner_iid(domain)
	        user_vector[inner_iid] = rating
	    except ValueError:
	        continue
	predicted_vector = np.matmul(np.matmul(user_vector,item_latent),item_latent_transpose)

	predicted_rating = {}
	for index,row in pd_hometimeline_urls.iterrows():
	    if row['tagged_urls'] != 'NA':
	        inner_iid = trainset.to_inner_iid(row['tagged_urls'])
	        predicted_rating[row['tweet_id']] = predicted_vector[inner_iid]

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
	ng_domains = integrate_NG_iffy(ng_fn,iffyfile)
	training_ng_domains_file = '../data/domain_idf.json'
	with open(training_ng_domains_file) as fn:
		domain_idf_dict = json.load(fn)
	training_ng_domains = domain_idf_dict.keys()
	#training_ng_domains_file = '../data/hoaxy_dataset_training_domains.csv'
	#training_ng_domains = pd.read_csv(training_ng_domains_file)['Domains'].values.tolist()

	print("Preparing Training set")
	hoaxy_training_file = '../data/hoaxy_dataset_training_tfidf.csv'
	pd_hoaxy_training_dataset = pd.read_csv(hoaxy_training_file)
	pd_hoaxy_training_dataset = pd_hoaxy_training_dataset.drop(columns=['Unnamed: 0'])
	reader = surprise.reader.Reader(rating_scale=(0, 1))
	training_data = surprise.dataset.Dataset.load_from_df(pd_hoaxy_training_dataset, reader) 
	trainset = training_data.build_full_trainset()

	print("Preparing model")
	model_file = '../model/hoaxy_recsys_model_tfidf.sav'
	algo = joblib.load(model_file)

	app.run(host = "0.0.0.0", port = 5053)