#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:41:00 2023

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
import surprise
from collections import Counter
from multiprocessing import Manager
from multiprocessing.dummy import Pool

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

def idf(values,tot_users=0):
    num_users = len(set(values))
    return math.log10(tot_users/num_users)

def tfidf(values,idf_dict={}):
    domain_counter = Counter(values)
    domain_rating = {}
    for dd in domain_counter.keys():
        tf = domain_counter[dd]/len(values)
        idf = idf_dict[dd]
        domain_rating[dd] = tf/idf
    domain_rating_json = json.dumps(domain_rating, indent = 4)
    return domain_rating_json

def rating_calculate(values):
    domain_rating = {}
    total = len(values)
    if total == 1:
        domain_rating[values.tolist()[0]] = 1.0
    else:
        total_log = math.log10(total)
        domain_counter = Counter(values)
        for dd in domain_counter.keys():
            fracc = 0.1
            if domain_counter[dd] > 1:
                fracc = math.log10(domain_counter[dd])
            rating_log = float(fracc)/float(total_log)
            domain_rating[dd] = rating_log
    domain_rating_json = json.dumps(domain_rating, indent = 4)
    return domain_rating_json

def get_data_from_new_users(data_dir,ng_domains):
    cwd = os.getcwd()
    os.chdir(data_dir)
    user_timeline_files = []
    for fn in glob.glob("*-user.json.gz"):
        user_timeline_files.append(fn)
    fave_timeline_files = []
    for fn in glob.glob("*-fave.json.gz"):
        fave_timeline_files.append(fn)
    os.chdir(cwd)
    
    users = []
    engaged_urls = []
    
    for fn in user_timeline_files:
        with gzip.open(data_dir + fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            if data['userTweets']:
                user_id = data["userObject"]["screen_name"]
                for tweet in data['userTweets']:
                    if 'retweeted_status' in tweet:
                        urls_extracted = extractfromentities(tweet['retweeted_status'])
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet['retweeted_status']:
                            urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                    else:
                        if 'quoted_status' in tweet:
                            urls_extracted = extractfromentities(tweet['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                        urls_extracted = extractfromentities(tweet)
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                            
    for fn in fave_timeline_files:
        with gzip.open(data_dir + fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            if data['likedTweets']:
                user_id = data["userObject"]["screen_name"]
                for tweet in data['likedTweets']:
                    if 'retweeted_status' in tweet:
                        urls_extracted = extractfromentities(tweet['retweeted_status'])
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet['retweeted_status']:
                            urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                    else:
                        urls_extracted = extractfromentities(tweet)
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet:
                            urls_extracted = extractfromentities(tweet['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
    
    engaged_urls_tagged = unshorten_and_tag_NG(engaged_urls,ng_domains)
    
    new_users_training = []
    new_domains_training = []
    
    for i in range(len(users)):
        if engaged_urls_tagged[i] != 'NA':
            new_users_training.append(users[i])
            new_domains_training.append(engaged_urls_tagged[i])
    
    pd_new_users = pd.concat([pd.DataFrame(new_users_training),pd.DataFrame(new_domains_training)],axis=1)
    return pd_new_users

ng_fn = "../NewsGuardIffy/label-2022101916.json"
iffyfile = "../NewsGuardIffy/iffy.csv"
ng_domains = integrate_NG_iffy(ng_fn,iffyfile)

recsys_engagement = pd.read_csv('../data/hoaxy_dataset.csv')
if 'Unnamed: 0' in recsys_engagement.columns:
    recsys_engagement = recsys_engagement.drop(columns=['Unnamed: 0'])
recsys_engagement = recsys_engagement.reset_index(drop=True)
data_dir = '/home/saumya/Documents/Infodiversity/pilot_data/pilot2_testing_engagement/'
pd_new_users = get_data_from_new_users(data_dir, ng_domains)
pd_new_users = pd_new_users.reset_index(drop=True)
pd_new_users.columns = ['user','NG_domain']
recsys_engagement = pd.concat([recsys_engagement,pd_new_users],ignore_index=True)

tot_users = len(recsys_engagement['user'].unique())
domain_idf = recsys_engagement.groupby('NG_domain').user.agg(idf,tot_users=tot_users)
domain_idf_dict = {}
for kk in domain_idf.keys():
    domain_idf_dict[kk] = domain_idf[kk]

domain_rating_json_column = recsys_engagement.groupby('user').NG_domain.agg(tfidf,idf_dict=domain_idf_dict)

#domain_rating_json_column = recsys_engagement.groupby('user').NG_domain.agg(rating_calculate)

#all_users = []
#for uu in domain_rating_json_column.index:
#    rating_json = json.loads(domain_rating_json_column[uu])
#    if 'domain' not in rating_json.keys():
#        all_users.append(uu)

users_training = []
domains_training = []
ratings_training = []

#Full training set
for (i,uu) in enumerate(domain_rating_json_column.keys()):
    if i % 10000 == 0:
        print(i)
    rating_json = json.loads(domain_rating_json_column[uu])
    for dd in rating_json.keys():
        users_training.append(uu)
        domains_training.append(dd)
        ratings_training.append(rating_json[dd])

pd_training = pd.concat([pd.DataFrame(users_training),pd.DataFrame(domains_training),pd.DataFrame(ratings_training)],axis=1)
pd_training.columns = ['Users','Domains','Ratings']
#pd_training_domains = pd.DataFrame(pd_training['Domains'].unique().tolist(),columns=['Domains'])

pd_training.to_csv('../data/hoaxy_dataset_training_tfidf.csv')
#pd_training_domains.to_csv('../data/hoaxy_dataset_training_domains_2.csv')

with open('../data/domain_idf.json','w') as fp:
    json.dump(domain_idf_dict,fp)

reader = surprise.reader.Reader(rating_scale=(0, 1))
data = surprise.dataset.Dataset.load_from_df(pd_training, reader)

algo = surprise.SVD()
trainset = data.build_full_trainset()
algo.fit(trainset)

model_filename = '../model/hoaxy_recsys_model_tfidf.sav'
joblib.dump(algo,model_filename)