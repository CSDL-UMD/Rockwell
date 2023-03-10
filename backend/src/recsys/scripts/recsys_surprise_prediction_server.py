import re
import math
import glob
import gzip
import json
import requests
import joblib
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

@app.route('/recsys_rerank', methods=['GET'])
def recsys_rerank():
	print("HERE!!!!")
	payload = request.json
	hometimeline_str = payload[0]
	usertimeline_str = payload[1]
	hometimeline = json.loads(hometimeline_str)
	usertimeline = json.loads(usertimeline_str)

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

	hometimeline_urls_length = len(pd_hometimeline_urls)
	engagement_urls_length = len(engaged_urls)

	all_urls = pd_hometimeline_urls['url'].values.tolist() + engaged_urls

	all_urls_tagged = unshorten_and_tag_NG(all_urls,ng_domains,training_ng_domains)

	hometimeline_urls_tagged = all_urls_tagged[0:hometimeline_urls_length]
	engaged_urls_tagged = all_urls_tagged[hometimeline_urls_length:]

	pd_hometimeline_urls = pd.concat([pd_hometimeline_urls,pd.DataFrame(hometimeline_urls_tagged,columns=['tagged_urls'])],axis=1)

	domains = []
	ratings = []
	engaged_urls_tagged = [url for url in engaged_urls_tagged if url != 'NA']
	total = len(engaged_urls_tagged)
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
	        predicted_rating.append(predicted_vector[inner_iid])
	    else:
	        predicted_rating.append(-1000)

	return "Done!"

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
	print("Reading NewsGuard, Iffy and training domains")
	ng_fn = "../NewsGuardIffy/label-2022101916.json"
	iffyfile = "../NewsGuardIffy/iffy.csv"
	training_ng_domains_file = '../data/hoaxy_dataset_training_domains.csv'
	ng_domains = integrate_NG_iffy(ng_fn,iffyfile)
	training_ng_domains = pd.read_csv(training_ng_domains_file)['Domains'].values.tolist()

	print("Preparing Training set")
	hoaxy_training_file = '../data/hoaxy_dataset_training.csv'
	pd_hoaxy_training_dataset = pd.read_csv(hoaxy_training_file)
	pd_hoaxy_training_dataset = pd_hoaxy_training_dataset.drop(columns=['Unnamed: 0'])
	reader = surprise.reader.Reader(rating_scale=(0, 1))
	training_data = surprise.dataset.Dataset.load_from_df(pd_hoaxy_training_dataset, reader) 
	trainset = training_data.build_full_trainset()

	print("Preparing model")
	model_file = '../model/hoaxy_recsys_model.sav'
	algo = joblib.load(model_file)

	app.run(host = "0.0.0.0", port = 5053)