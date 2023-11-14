#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 10:17:32 2023

@author: saumya
"""

import re
import json
import pandas as pd
from multiprocessing import Manager
from multiprocessing.dummy import Pool

THREADS = 5

def init(queue):
    global idx
    idx = queue.get()

def getdomain(url):
    return ".".join(url.split("/")[2].split(".")[-2:])

def adddomainraw(df):
    return (df.assign(domain_raw=df.raw_url.apply(getdomain)))

def adddomain(df):
    return (df.assign(domain=df.URLS.apply(getdomain)))

def gettwitterhandle(url):
    try:
        return url.split("/")[3]
    except:
        return ""

def addtwitterNG(df):
    return (df.assign(twitter=df.twitter.apply(gettwitterhandle)))

def gettwitterhandleiftwitter(row):
    if row["domain"] == "twitter.com":
        return gettwitterhandle(row["URLS"])
    else:
        return ""

def addtwitterhandle(df):
    return df.assign(twitter=df.apply(gettwitterhandleiftwitter, axis=1))

def read_NewsGuard(ng_fn):
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
    
    ng_map_domain_rank = {}
    ng_map_twitter_rank = {}
    ng_map_domain_score = {}
    ng_map_twitter_score = {}
    
    for index,row in ng_domains.iterrows():
        ng_map_domain_rank[row['domain']] = row['rank']
        ng_map_domain_score[row['domain']] = row['score']
        if row['twitter'] != '' and row['twitter'] != 'i':
            ng_map_twitter_rank[row['twitter']] = row['rank']
            ng_map_twitter_score[row['twitter']] = row['score']
    
    return [ng_map_domain_rank,ng_map_twitter_rank,ng_map_domain_score,ng_map_twitter_score]

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
    
pd_hoaxy = pd.read_csv('/home/saumya/hoaxy_URLS.csv')
pd_hoaxy = adddomain(pd_hoaxy)
pd_hoaxy = addtwitterhandle(pd_hoaxy)
pd_hoaxy = pd_hoaxy.drop('Unnamed: 0',axis=1)
print("Read and Processed hoaxy")

ng_fn = "/home/saumya/label-2022101916.json"
iffyfile = "/home/saumya/iffy.csv"
ng_domains = integrate_NG_iffy(ng_fn,iffyfile)
ng_domain_values = ng_domains['domain'].unique()
ng_twitter_values = ng_domains['twitter'].unique()

def classify_NG_domain(hoaxy_row):
    global idx
    if hoaxy_row[0] % 10000 == 0:
        print(hoaxy_row[0])
    hoaxy_domain = hoaxy_row[1]['domain']
    hoaxy_twitter = hoaxy_row[1]['twitter']
    if hoaxy_domain in ng_domain_values and len(hoaxy_domain) > 1:
        return hoaxy_domain
    if hoaxy_twitter in ng_twitter_values and len(hoaxy_twitter) > 1:
        try:
            return ng_domains.loc[(ng_domains['twitter'] == hoaxy_twitter)]['domain'][0]
        except KeyError:
            return "NaN"
    return "NaN"

ids = list(range(THREADS))
manager = Manager()
idQueue = manager.Queue()

for i in ids:
    idQueue.put(i)

pool = Pool(THREADS,init,(idQueue,))
ng_domain_classified = []
for dd in pool.imap(classify_NG_domain,pd_hoaxy.iterrows()):
    ng_domain_classified.append(dd)

pd_hoaxy_new_idx = pd_hoaxy.reset_index()        
pd_hoaxy_tagged = pd.concat([pd_hoaxy_new_idx,pd.DataFrame(ng_domain_classified,columns=["NG_domain"])],axis=1)
pd_hoaxy_dropped = pd_hoaxy_tagged.drop(columns=['URLS','domain','twitter'])
pd_hoaxy_dropped = pd_hoaxy_dropped[pd_hoaxy_dropped.NG_domain != 'NaN']

pd_hoaxy_dropped.to_csv('/home/saumya/hoaxy_dataset_URLS_tagged.csv')