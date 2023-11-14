#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 14:16:36 2023

@author: saumya
"""

import re
import math
import json
import numpy as np
import pandas as pd
import surprise
from scipy.stats import sem
from collections import Counter

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

def gettwitterhandle(url):
    try:
        return url.split("/")[3]
    except:
        return ""

def addtwitterNG(df):
    return (df.assign(twitter=df.twitter.apply(gettwitterhandle)))

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

pd_hoaxy_URLS = pd.read_csv('/home/saumya/hoaxy_data_all/hoaxy_dataset_URLS_tagged.csv')
pd_hoaxy_URLS = pd_hoaxy_URLS.drop(columns=['Unnamed: 0'])
pd_hoaxy_URLS = pd_hoaxy_URLS.drop(columns=['index'])
pd_hoaxy_URLS.columns = ['Users','Items']

pd_hoaxy_handles = pd.read_csv('/home/saumya/hoaxy_data_all/hoaxy_handles_screennames.csv')
pd_hoaxy_handles = pd_hoaxy_handles.drop(columns=['Unnamed: 0'])
pd_hoaxy_handles.columns = ['Users','Items']
pd_hoaxy_handles = pd_hoaxy_handles.dropna()
pd_hoaxy_handles = pd_hoaxy_handles.reset_index(drop=True)

pd_training_pilots = pd.read_csv('/home/saumya/hoaxy_data_all/pilot1_pilot2_training.csv')
pd_training_pilots = pd_training_pilots.drop(columns=['Unnamed: 0'])

pd_training = pd.concat([pd_hoaxy_URLS,pd_hoaxy_handles,pd_training_pilots])

tot_users = len(pd_training['Users'].unique())
domain_idf = pd_training.groupby('Items').Users.agg(idf,tot_users=tot_users)
domain_idf_dict = {}
for kk in domain_idf.keys():
    domain_idf_dict[kk] = domain_idf[kk]
domain_rating_json_column = pd_training.groupby('Users').Items.agg(tfidf,idf_dict=domain_idf_dict)

print("LENGTH OF TRAINING SET : "+str(len(domain_rating_json_column.keys())))

users_training = []
domains_training = []
ratings_training = []

#Full training set
for (i,uu) in enumerate(domain_rating_json_column.keys()):
    if i % 10000 == 0:
        print(i/10000)
    rating_json = json.loads(domain_rating_json_column[uu])
    for dd in rating_json.keys():
        users_training.append(uu)
        domains_training.append(dd)
        ratings_training.append(rating_json[dd])

pd_training_rating = pd.concat([pd.DataFrame(users_training),pd.DataFrame(domains_training),pd.DataFrame(ratings_training)],axis=1)
pd_training_rating.columns = ['Users','Domains','Ratings']

reader = surprise.reader.Reader(rating_scale=(0, 1))
data = surprise.dataset.Dataset.load_from_df(pd_training_rating, reader)

algo = surprise.SVD()
trainset = data.build_full_trainset()
algo.fit(trainset)

pd_testing_pilots = pd.read_csv('/home/saumya/hoaxy_data_all/pilot1_pilot2_testing.csv')
pd_testing_pilots = pd_testing_pilots.drop(columns=['Unnamed: 0'])

pd_testing_pilots_without_tweets = pd_testing_pilots.drop(columns=['TweetID','Age'])

pd_all = pd.concat([pd_hoaxy_URLS,pd_hoaxy_handles,pd_training_pilots,pd_testing_pilots_without_tweets])
tot_users_all = len(pd_all['Users'].unique())
domain_idf_all = pd_all.groupby('Items').Users.agg(idf,tot_users=tot_users_all)
domain_idf_dict_all = {}
for kk in domain_idf_all.keys():
    domain_idf_dict_all[kk] = domain_idf_all[kk]
domain_rating_json_column_all = pd_all.groupby('Users').Items.agg(tfidf,idf_dict=domain_idf_dict_all)

print("LENGTH OF THE WHOLE SET : "+str(len(domain_rating_json_column_all.keys())))

users_training_all = []
domains_training_all = []
ratings_training_all = []

#Full training set
for (i,uu) in enumerate(domain_rating_json_column_all.keys()):
    if i % 10000 == 0:
        print(i/10000)
    rating_json = json.loads(domain_rating_json_column_all[uu])
    for dd in rating_json.keys():
        users_training_all.append(uu)
        domains_training_all.append(dd)
        ratings_training_all.append(rating_json[dd])

pd_all_rating = pd.concat([pd.DataFrame(users_training_all),pd.DataFrame(domains_training_all),pd.DataFrame(ratings_training_all)],axis=1)
pd_all_rating.columns = ['Users','Domains','Ratings']

alpha_m = 0.9
alpha_t = 0.1

testing_users = pd_testing_pilots['Users'].unique().tolist()

pd_all_rating_testing = pd_all_rating.loc[pd_all_rating['Users'].isin(testing_users)]

users_predicted = []
items_predicted = []
tweetids_predicted = []
age_predicted = []
norm_age_predicted = []
actual_rating_predicted = []
recsys_predicted = []
recsys_age_predicted = []

for tu in testing_users:
    pd_tu = pd_testing_pilots.loc[pd_testing_pilots['Users'] == tu]
    pd_tu['rating_age'] = np.exp(-1.0*pd_tu['Age']/pd_tu['Age'].mean())
    for index,row in pd_tu.iterrows():
        try:
            recsys_rating = algo.predict(uid=row['Users'], iid=row['Items']).est
            predicted_rating = alpha_m*recsys_rating + alpha_t*row['rating_age']
            actual_rating = pd_all_rating_testing.loc[(pd_all_rating_testing['Users'] == tu) & (pd_all_rating_testing['Domains'] == row['Items'])]['Ratings'].values[0]
            users_predicted.append(row['Users'])
            items_predicted.append(row['Items'])
            tweetids_predicted.append(row['TweetID'])
            age_predicted.append(row['Age'])
            norm_age_predicted.append(row['rating_age'])
            actual_rating_predicted.append(actual_rating)
            recsys_predicted.append(recsys_rating)
            recsys_age_predicted.append(predicted_rating)
        except ValueError:
            continue

pd_predicted = pd.concat([pd.DataFrame(users_predicted,columns=['Users']),
                          pd.DataFrame(items_predicted,columns=['Items']),
                          pd.DataFrame(tweetids_predicted,columns=['TweetID']),
                          pd.DataFrame(age_predicted,columns=['Age']),
                          pd.DataFrame(norm_age_predicted,columns=['Age_Normalized']),
                          pd.DataFrame(actual_rating_predicted,columns=['Actual_Rating']),
                          pd.DataFrame(recsys_predicted,columns=['Recsys_Rating']),
                          pd.DataFrame(recsys_age_predicted,columns=['Recsys_Age_Rating'])],axis=1)

predicted_users = pd_predicted['Users'].unique()

precisionk_prediction = []
precisionk_prediction_recency = []
precisionk_recency = []
for (idx,uu) in enumerate(predicted_users):
    pd_uu = pd_predicted.loc[pd_predicted['Users'] == uu]
    tweets = pd_uu['TweetID'].values
    actual_ratings = pd_uu['Actual_Rating'].values
    predicted_ratings = pd_uu['Recsys_Rating'].values
    predicted_ratings_recency = pd_uu['Recsys_Age_Rating'].values
    recency = pd_uu['Age'].values
    actual_rantings_sorted = [x for _, x in sorted(zip(actual_ratings, tweets), key=lambda pair: pair[0], reverse=True)]
    predicted_rantings_sorted = [x for _, x in sorted(zip(predicted_ratings, tweets), key=lambda pair: pair[0], reverse=True)]
    predicted_recency_rantings_sorted = [x for _, x in sorted(zip(predicted_ratings_recency, tweets), key=lambda pair: pair[0], reverse=True)]
    recency_rantings_sorted = [x for _, x in sorted(zip(recency, tweets), key=lambda pair: pair[0])]
    precisionk_prediction_user = []
    precisionk_prediction_recency_user = []
    precisionk_recency_user = []
    for k in range(1,len(tweets)+1):
        TP_prediction = 0
        TP_prediction_recency = 0
        TP_recency = 0
        actual_ratings_sorted_k = actual_rantings_sorted[0:k]
        for ii in range(k):
            if predicted_rantings_sorted[ii] in actual_ratings_sorted_k:
                TP_prediction = TP_prediction + 1
            if predicted_recency_rantings_sorted[ii] in actual_ratings_sorted_k:
                TP_prediction_recency = TP_prediction_recency + 1
            if recency_rantings_sorted[ii] in actual_ratings_sorted_k:
                TP_recency = TP_recency + 1
        precisionk_prediction_user.append(TP_prediction/k)
        precisionk_prediction_recency_user.append(TP_prediction_recency/k)
        precisionk_recency_user.append(TP_recency/k)
    precisionk_prediction.append(precisionk_prediction_user)
    precisionk_prediction_recency.append(precisionk_prediction_recency_user)
    precisionk_recency.append(precisionk_recency_user)

k = []
prediction_k = []
prediction_k_err = []
prediction_recency_k = []
prediction_recency_k_err = []
recency_k = []
recency_k_err = []
k_itr = 1
while True:
    print(k_itr)
    prediction_k_itr = []
    prediction_recency_k_itr = []
    recency_k_itr = []
    for i in range(len(precisionk_prediction)):
        if k_itr < len(precisionk_prediction[i]):
            prediction_k_itr.append(precisionk_prediction[i][k_itr - 1])
            prediction_recency_k_itr.append(precisionk_prediction_recency[i][k_itr - 1])
            recency_k_itr.append(precisionk_recency[i][k_itr - 1])
    if len(prediction_k_itr) == 0:
        break
    k.append(k_itr)
    prediction_k.append(sum(prediction_k_itr)/len(prediction_k_itr))
    prediction_k_err.append(sem(prediction_k_itr))
    prediction_recency_k.append(sum(prediction_recency_k_itr)/len(prediction_recency_k_itr))
    prediction_recency_k_err.append(sem(prediction_recency_k_itr))
    recency_k.append(sum(recency_k_itr)/len(recency_k_itr))
    recency_k_err.append(sem(recency_k_itr))
    k_itr += 1

ng_fn = "/home/saumya/label-2022101916.json"
iffyfile = "/home/saumya/iffy.csv"
ng_domains = integrate_NG_iffy(ng_fn,iffyfile)

trustworthinessk_prediction = []
trustworthinessk_prediction_recency = []
trustworthinessk_recency = []
trustworthinessk_actual = []
for (idx,uu) in enumerate(predicted_users):
    pd_uu = pd_predicted.loc[pd_predicted['Users'] == uu]
    tweets = pd_uu['Items'].values
    actual_ratings = pd_uu['Actual_Rating'].values
    predicted_ratings = pd_uu['Recsys_Rating'].values
    predicted_ratings_recency = pd_uu['Recsys_Age_Rating'].values
    recency = pd_uu['Age'].values
    actual_rantings_sorted = [x for _, x in sorted(zip(actual_ratings, tweets), key=lambda pair: pair[0], reverse=True)]
    predicted_rantings_sorted = [x for _, x in sorted(zip(predicted_ratings, tweets), key=lambda pair: pair[0], reverse=True)]
    predicted_recency_rantings_sorted = [x for _, x in sorted(zip(predicted_ratings_recency, tweets), key=lambda pair: pair[0], reverse=True)]
    recency_rantings_sorted = [x for _, x in sorted(zip(recency, tweets), key=lambda pair: pair[0])]
    trustworthy_domains = ng_domains.loc[ng_domains['rank'] == 'T']['domain'].unique().tolist()
    trustworthinessk_prediction_user = []
    trustworthinessk_prediction_recency_user = []
    trustworthinessk_recency_user = []
    trustworthinessk_actual_user = []
    for k in range(1,len(tweets)+1):
        TP_prediction = 0
        TP_prediction_recency = 0
        TP_recency = 0
        TP_actual = 0
        for ii in range(k):
            if predicted_rantings_sorted[ii] in trustworthy_domains:
                TP_prediction = TP_prediction + 1
            if predicted_recency_rantings_sorted[ii] in trustworthy_domains:
                TP_prediction_recency = TP_prediction_recency + 1
            if recency_rantings_sorted[ii] in trustworthy_domains:
                TP_recency = TP_recency + 1
            if actual_rantings_sorted[ii] in trustworthy_domains:
                TP_actual = TP_actual + 1
        trustworthinessk_prediction_user.append(TP_prediction/k)
        trustworthinessk_prediction_recency_user.append(TP_prediction_recency/k)
        trustworthinessk_recency_user.append(TP_recency/k)
        trustworthinessk_actual_user.append(TP_actual/k)
    trustworthinessk_prediction.append(trustworthinessk_prediction_user)
    trustworthinessk_prediction_recency.append(trustworthinessk_prediction_recency_user)
    trustworthinessk_recency.append(trustworthinessk_recency_user)
    trustworthinessk_actual.append(trustworthinessk_actual_user)

k = []
prediction_k = []
prediction_k_err = []
prediction_recency_k = []
prediction_recency_k_err = []
recency_k = []
recency_k_err = []
actual_k = []
actual_k_err = []
k_itr = 1
while True:
    print(k_itr)
    prediction_k_itr = []
    prediction_recency_k_itr = []
    recency_k_itr = []
    actual_k_itr = []
    for i in range(len(trustworthinessk_prediction)):
        if k_itr < len(trustworthinessk_prediction[i]):
            prediction_k_itr.append(trustworthinessk_prediction[i][k_itr - 1])
            prediction_recency_k_itr.append(trustworthinessk_prediction_recency[i][k_itr - 1])
            recency_k_itr.append(trustworthinessk_recency[i][k_itr - 1])
            actual_k_itr.append(trustworthinessk_actual[i][k_itr - 1])
    if len(prediction_k_itr) == 0:
        break
    k.append(k_itr)
    prediction_k.append(sum(prediction_k_itr)/len(prediction_k_itr))
    prediction_k_err.append(sem(prediction_k_itr))
    prediction_recency_k.append(sum(prediction_recency_k_itr)/len(prediction_recency_k_itr))
    prediction_recency_k_err.append(sem(prediction_recency_k_itr))
    recency_k.append(sum(recency_k_itr)/len(recency_k_itr))
    recency_k_err.append(sem(recency_k_itr))
    actual_k.append(sum(actual_k_itr)/len(actual_k_itr))
    actual_k_err.append(sem(actual_k_itr))
    k_itr += 1

trustworthiness_score_prediction = []
trustworthinessk_score_prediction_recency = []
trustworthinessk_score_recency = []
trustworthinessk_score_actual = []
for (idx,uu) in enumerate(predicted_users):
    print(idx)
    pd_uu = pd_predicted.loc[pd_predicted['Users'] == uu]
    tweets = pd_uu['Items'].values
    actual_ratings = pd_uu['Actual_Rating'].values
    predicted_ratings = pd_uu['Recsys_Rating'].values
    predicted_ratings_recency = pd_uu['Recsys_Age_Rating'].values
    recency = pd_uu['Age'].values
    actual_rantings_sorted = [x for _, x in sorted(zip(actual_ratings, tweets), key=lambda pair: pair[0], reverse=True)]
    predicted_rantings_sorted = [x for _, x in sorted(zip(predicted_ratings, tweets), key=lambda pair: pair[0], reverse=True)]
    predicted_recency_rantings_sorted = [x for _, x in sorted(zip(predicted_ratings_recency, tweets), key=lambda pair: pair[0], reverse=True)]
    recency_rantings_sorted = [x for _, x in sorted(zip(recency, tweets), key=lambda pair: pair[0])]
    trustworthy_domains = ng_domains.loc[ng_domains['rank'] == 'T']['domain'].unique().tolist()
    trustworthiness_score_prediction_user = []
    trustworthiness_score_prediction_recency_user = []
    trustworthiness_score_recency_user = []
    trustworthiness_score_actual_user = []
    for k in range(1,len(tweets)+1):
        score_prediction = 0
        score_prediction_recency = 0
        score_recency = 0
        score_actual = 0
        for ii in range(k):
            score_prediction = score_prediction + ng_domains.loc[ng_domains['domain'] == predicted_rantings_sorted[ii]]['score'].values[0]
            score_prediction_recency = score_prediction_recency + ng_domains.loc[ng_domains['domain'] == predicted_recency_rantings_sorted[ii]]['score'].values[0]
            score_recency = score_recency + ng_domains.loc[ng_domains['domain'] == recency_rantings_sorted[ii]]['score'].values[0]
            score_actual = score_actual + ng_domains.loc[ng_domains['domain'] == actual_rantings_sorted[ii]]['score'].values[0]
        trustworthiness_score_prediction_user.append(score_prediction/k)
        trustworthiness_score_prediction_recency_user.append(score_prediction_recency/k)
        trustworthiness_score_recency_user.append(score_recency/k)
        trustworthiness_score_actual_user.append(score_actual/k)
    trustworthiness_score_prediction.append(trustworthiness_score_prediction_user)
    trustworthinessk_score_prediction_recency.append(trustworthiness_score_prediction_recency_user)
    trustworthinessk_score_recency.append(trustworthiness_score_recency_user)
    trustworthinessk_score_actual.append(trustworthiness_score_actual_user)

k = []
prediction_k = []
prediction_k_err = []
prediction_recency_k = []
prediction_recency_k_err = []
recency_k = []
recency_k_err = []
actual_k = []
actual_k_err = []
k_itr = 1
while True:
    print(k_itr)
    prediction_k_itr = []
    prediction_recency_k_itr = []
    recency_k_itr = []
    actual_k_itr = []
    for i in range(len(trustworthiness_score_prediction)):
        if k_itr < len(trustworthiness_score_prediction[i]):
            prediction_k_itr.append(trustworthiness_score_prediction[i][k_itr - 1])
            prediction_recency_k_itr.append(trustworthinessk_score_prediction_recency[i][k_itr - 1])
            recency_k_itr.append(trustworthinessk_score_recency[i][k_itr - 1])
            actual_k_itr.append(trustworthinessk_score_actual[i][k_itr - 1])
    if len(prediction_k_itr) == 0:
        break
    k.append(k_itr)
    prediction_k.append(sum(prediction_k_itr)/len(prediction_k_itr))
    prediction_k_err.append(sem(prediction_k_itr))
    prediction_recency_k.append(sum(prediction_recency_k_itr)/len(prediction_recency_k_itr))
    prediction_recency_k_err.append(sem(prediction_recency_k_itr))
    recency_k.append(sum(recency_k_itr)/len(recency_k_itr))
    recency_k_err.append(sem(recency_k_itr))
    actual_k.append(sum(actual_k_itr)/len(actual_k_itr))
    actual_k_err.append(sem(actual_k_itr))
    k_itr += 1

import matplotlib.pyplot as plt
plt.errorbar(k[0:30],prediction_k[0:30], prediction_k_err[0:30], label='CF')
plt.errorbar(k[0:30],prediction_recency_k[0:30], prediction_recency_k_err[0:30], label='CF+Recency')
plt.errorbar(k[0:30],recency_k[0:30], recency_k_err[0:30], label='Recency')
plt.errorbar(k[0:30],actual_k[0:30], actual_k_err[0:30], label='Actual visits')
plt.legend()