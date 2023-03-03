#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:41:00 2023

@author: saumya
"""

import pandas as pd
import math
import json
import joblib
import surprise
from collections import Counter

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

recsys_engagement = pd.read_csv('../data/hoaxy_dataset.csv')
domain_rating_json_column = recsys_engagement.groupby('user').NG_domain.agg(rating_calculate)

all_users = []
for uu in domain_rating_json_column.index:
    rating_json = json.loads(domain_rating_json_column[uu])
    if 'domain' not in rating_json.keys():
        all_users.append(uu)

users_training = []
domains_training = []
ratings_training = []

#Full training set
for (i,uu) in enumerate(all_users):
    if i % 10000 == 0:
        print(i)
    rating_json = json.loads(domain_rating_json_column[uu])
    for dd in rating_json.keys():
        users_training.append(uu)
        domains_training.append(dd)
        ratings_training.append(rating_json[dd])

pd_training = pd.concat([pd.DataFrame(users_training),pd.DataFrame(domains_training),pd.DataFrame(ratings_training)],axis=1)
pd_training.columns = ['Users','Domains','Ratings']
pd_training_domains = pd.DataFrame(pd_training['Domains'].unique().tolist(),columns=['Domains'])

pd_training.to_csv('../data/hoaxy_dataset_training.csv')
pd_training_domains.to_csv('../data/hoaxy_dataset_training_domains.csv')

reader = surprise.reader.Reader(rating_scale=(0, 1))
data = surprise.dataset.Dataset.load_from_df(pd_training, reader)

algo = surprise.SVD()
trainset = data.build_full_trainset()
algo.fit(trainset)

model_filename = '../model/hoaxy_recsys_model.sav'
joblib.dump(algo,model_filename)