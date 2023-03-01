#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 16 11:07:57 2023

@author: saumya
"""

import re
import json
import pandas as pd

def getdomain(url):
    return ".".join(url.split("/")[2].split(".")[-2:])

def adddomainraw(df):
    return (df.assign(domain_raw=df.raw_url.apply(getdomain)))

def adddomain(df):
    return (df.assign(domain=df.unshorten_url.apply(getdomain)))

def gettwitterhandle(url):
    try:
        return url.split("/")[3]
    except:
        return ""

def addtwitterNG(df):
    return (df.assign(twitter=df.twitter.apply(gettwitterhandle)))

def gettwitterhandleiftwitter(row):
    if row["domain"] == "twitter.com":
        return gettwitterhandle(row["unshorten_url"])
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

pd_hoaxy_second_half = pd.read_csv('../data/recsys_training_data_final_unshortened.csv')
pd_hoaxy_second_half = adddomain(pd_hoaxy_second_half)
pd_hoaxy_second_half = adddomainraw(pd_hoaxy_second_half)
pd_hoaxy_second_half = addtwitterhandle(pd_hoaxy_second_half)

pd_hoaxy_first_half = pd.read_csv('../data/recsys_training_data_first_half.csv')
pd_hoaxy_first_half['unshorten_url'] = pd_hoaxy_first_half.loc[:, 'raw_url']
pd_hoaxy_first_half = adddomain(pd_hoaxy_first_half)
pd_hoaxy_first_half = adddomainraw(pd_hoaxy_first_half)
pd_hoaxy_first_half = addtwitterhandle(pd_hoaxy_first_half)

pd_hoaxy = pd.concat([pd_hoaxy_first_half,pd_hoaxy_second_half])

ng_fn = "../data/label-2022101916.json"
iffyfile = "../data/iffy.csv"
ng_domains = integrate_NG_iffy(ng_fn,iffyfile)

#count users for each NG domain
"""
user_counts = []
for index,row in ng_domains.iterrows():
    print(index)
    ng_iffy_domain = row['domain']
    ng_twitter = row['twitter']
    unique_users = 0
    if len(ng_twitter) > 0:
        unique_users = pd_hoaxy.loc[(pd_hoaxy['domain_raw'] == ng_iffy_domain) | (pd_hoaxy['domain'] == ng_iffy_domain) | (pd_hoaxy['twitter'] == ng_twitter)]['user'].unique().size
    else:
        unique_users = pd_hoaxy.loc[(pd_hoaxy['domain_raw'] == ng_iffy_domain) | (pd_hoaxy['domain'] == ng_iffy_domain)]['user'].unique().size
    user_counts.append(unique_users)
"""

ng_domain_column = []
ng_domain_values = ng_domains['domain'].unique()
ng_twitter_values = ng_domains['twitter'].unique()
for index,row in pd_hoaxy.iterrows():
    if row['domain'] in ng_domain_values:
        ng_domain_column.append(row['domain'])
    elif row['domain_raw'] in ng_domain_values:
        ng_domain_column.append(row['domain_raw'])
    elif row['twitter'] in ng_twitter_values:
        try:
            ng_domain_column.append(ng_domains.loc[(ng_domains['twitter'] == row['twitter'])]['domain'][0])
        except KeyError:
            ng_domain_column.append("NaN")
    else:
        ng_domain_column.append("NaN")

pd_hoaxy_new_idx = pd_hoaxy.reset_index()        
pd_hoaxy_tagged = pd.concat([pd_hoaxy_new_idx,pd.DataFrame(ng_domain_column,columns=["NG_domain"])],axis=1)
pd_hoaxy_dropped = pd_hoaxy_tagged.drop(columns=['index','raw_url','unshorten_url','domain','domain_raw','twitter','Unnamed: 0'])
pd_hoaxy_dropped = pd_hoaxy_dropped[pd_hoaxy_dropped.NG_domain != 'NaN']

pd_hoaxy_dropped.to_csv('../data/hoaxy_dataset.csv')