#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  4 02:00:48 2021

@author: saumya
"""

import pandas as pd
import numpy as np
import math
import json
import random
import operator
import surprise
from scipy import stats
from scipy.spatial.distance import cosine
from collections import Counter

def rating_calculate(values):
    domain_rating = {}
    total = len(values)
    if total == 1:
        domain_rating['domain'] = -1
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

def precision_at_k(pd_prediction):
    users = pd_prediction['Users'].unique().tolist()
    precision_array = []
    precision_array_err = []
    for k in range(1,11):
        print(k)
        precision_at_k = []
        for i in range(len(users)):
            domains = pd_prediction.loc[pd_prediction['Users'] == users[i]]['Domains'].values.tolist()
            if len(domains) < k:
                continue
            actual_ratings = pd_prediction.loc[pd_prediction['Users'] == users[i]]['Ratings'].values.tolist()
            predicted_ratings = pd_prediction.loc[pd_prediction['Users'] == users[i]]['Predicted'].values.tolist()
            actual_domains_ranked = [x for _, x in sorted(zip(actual_ratings, domains), key=lambda pair: pair[0])]
            predicted_domains_ranked = [x for _, x in sorted(zip(predicted_ratings, domains), key=lambda pair: pair[0])]
            actual_domains_ranked = actual_domains_ranked[0:k]
            predicted_domains_ranked = predicted_domains_ranked[0:k]
            accurate_domains = 0
            for j in range(k):
                if predicted_domains_ranked[j] in actual_domains_ranked:
                    accurate_domains = accurate_domains + 1
            precision_at_k.append(float(accurate_domains)/float(k))
        if not precision_at_k:
            break
        else:
            precision_array.append(sum(precision_at_k)/len(precision_at_k))
            precision_array_err.append(stats.sem(precision_at_k))

def rmse_at_k(pd_prediction):
    users = pd_prediction['Users'].unique().tolist()
    rmse_array = []
    rmse_array_err = []
    for k in range(1,11):
        print(k)
        rmse_at_k = []
        for i in range(len(users)):
            domains = pd_prediction.loc[pd_prediction['Users'] == users[i]]['Domains'].values.tolist()
            if len(domains) < k:
                continue
            actual_ratings = pd_prediction.loc[pd_prediction['Users'] == users[i]]['Ratings'].values.tolist()
            predicted_ratings = pd_prediction.loc[pd_prediction['Users'] == users[i]]['Predicted'].values.tolist()
            actual_ratings_map = {}
            predicted_ratings_map = {}
            for j in range(len(domains)):
                actual_ratings_map[domains[j]] = actual_ratings[j]
                predicted_ratings_map[domains[j]] = predicted_ratings[j]
            predicted_domains_ranked = [x for _, x in sorted(zip(predicted_ratings, domains), key=lambda pair: pair[0])]
            predicted_domains_ranked = predicted_domains_ranked[0:k]
            tot_rmse = 0.0
            for j in range(k):
                tot_rmse = tot_rmse + math.pow((actual_ratings_map[predicted_domains_ranked[j]] - predicted_ratings_map[predicted_domains_ranked[j]]),2)
            tot_rmse = float(tot_rmse)/float(k)
            tot_rmse = math.sqrt(tot_rmse)
            rmse_at_k.append(tot_rmse)
        if not rmse_at_k:
            break
        else:
            rmse_array.append(sum(rmse_at_k)/len(rmse_at_k))
            rmse_array_err.append(stats.sem(rmse_at_k))

recsys_engagement = pd.read_csv('/home/saumya/Documents/USF/Project/ASD/recommendation_surprise/user_domain_reaction.csv',sep='\t')
domain_rating_json_column = recsys_engagement.groupby('Users').Domains.agg(rating_calculate)

all_users = []
for uu in domain_rating_json_column.index:
    rating_json = json.loads(domain_rating_json_column[uu])
    if 'domain' not in rating_json.keys():
        all_users.append(uu)

test_users =  random.sample(all_users,int(0.3*(len(all_users))))

users_training = []
domains_training = []
ratings_training = []

users_testing = []
domains_testing = []
ratings_testing = []

#Full training set
for (i,uu) in enumerate(all_users):
    if i % 10000 == 0:
        print(i)
    rating_json = json.loads(domain_rating_json_column[uu])
    for dd in rating_json.keys():
        users_training.append(uu)
        domains_training.append(dd)
        ratings_training.append(rating_json[dd])

for (i,uu) in enumerate(all_users):
    if i % 100 == 0:
        print(i)
    rating_json = json.loads(domain_rating_json_column[uu])
    test_domains = []
    if uu in test_users:
        all_domains = list(rating_json.keys())
        test_domains = random.sample(all_domains,int(0.3*len(all_domains)))
    for dd in rating_json.keys():
        if dd in test_domains:
            users_testing.append(uu)
            domains_testing.append(dd)
            ratings_testing.append(rating_json[dd])
        else:
            users_training.append(uu)
            domains_training.append(dd)
            ratings_training.append(rating_json[dd])

pd_training = pd.concat([pd.DataFrame(users_training),pd.DataFrame(domains_training),pd.DataFrame(ratings_training)],axis=1)
pd_training.columns = ['Users','Domains','Ratings']
pd_testing = pd.concat([pd.DataFrame(users_testing),pd.DataFrame(domains_testing),pd.DataFrame(ratings_testing)],axis=1)
pd_testing.columns = ['Users','Domains','Ratings']


pd_training = pd.read_csv('/home/saumya/Documents/USF/Project/ASD/recommendation_surprise/recsys_training.csv')
pd_testing = pd.read_csv('/home/saumya/Documents/USF/Project/ASD/recommendation_surprise/recsys_testing.csv')

pd_testing_series = pd_testing.groupby('Users')['Domains'].count()
training_users = pd_training['Users'].unique()
pd_testing_max_users = pd_testing_series.nlargest(500)
max_users_testing = pd_testing_max_users.index.values.tolist()
pd_training_series = pd_training.groupby('Users')['Domains'].count()
pd_training_max_users = pd_training_series.nlargest(10000)
max_users_training = pd_training_max_users.index.values.tolist()
for u_test in max_users_testing:
    if u_test in training_users:
        max_users_training.append(u_test)
max_users_training = list(set(max_users_training))

pd_training = pd_training.loc[pd_training['Users'].isin(max_users_training)].reset_index().drop(['index'],axis=1)
pd_testing = pd_testing.loc[pd_testing['Users'].isin(max_users_testing)].reset_index().drop(['index'],axis=1)

reader = surprise.reader.Reader(rating_scale=(0, 1))
data = surprise.dataset.Dataset.load_from_df(pd_training, reader)
data_test = surprise.dataset.Dataset.load_from_df(pd_testing, reader)

algo = surprise.SVD()
trainset = data.build_full_trainset()
algo.fit(trainset)

prediction_surprise = []

for index,row in pd_testing.iterrows():
    try:
        inner_uid = trainset.to_inner_uid(row['Users'])
        inner_iid = trainset.to_inner_iid(row['Domains'])
        prediction_surprise.append(algo.predict(uid=row['Users'], iid=row['Domains']).est)
    except ValueError:
        prediction_surprise.append(-1000)

pd_surprise_results = pd.concat([pd_testing,pd.DataFrame(prediction_surprise)],axis=1)
pd_surprise_results.columns = ['Users','Domains','Ratings','Predicted']
pd_surprise_results.to_csv('/home/saumya/Documents/USF/Project/ASD/recommendation_surprise/results_surprise.csv',encoding='utf-8',index=False)

users_in_testing = pd_testing['Users'].unique()

pd_training_remove = pd_training.drop(pd_training[pd_training['Users'].isin(users_in_testing)].index)

data_latent = surprise.dataset.Dataset.load_from_df(pd_training_remove, reader)

algo_latent = surprise.SVD()
trainset_latent = data_latent.build_full_trainset()
algo_latent.fit(trainset_latent)

item_latent = algo_latent.qi
item_latent_transpose = np.matrix.transpose(item_latent)
vector_len = item_latent.shape[0]

predicted_latent_dict = {}

for (i,test_uu) in enumerate(users_in_testing):
    if i%100 == 0:
        print(i)
    pd_user_training = pd_training.loc[pd_training['Users'] == test_uu]
    user_vector = np.zeros(vector_len)
    for index,row in pd_user_training.iterrows():
        domain_user = row['Domains']
        rating_user = row['Ratings']
        try:
            inner_iid = trainset_latent.to_inner_iid(domain_user)
            user_vector[inner_iid] = rating_user
        except ValueError:
            continue
    predicted_vector = np.matmul(np.matmul(user_vector,item_latent),item_latent_transpose)
    pd_user_testing = pd_testing.loc[pd_testing['Users'] == test_uu]
    for index,row in pd_user_testing.iterrows():
        domain_testing = row['Domains']
        try:
            inner_iid = trainset_latent.to_inner_iid(domain_testing)
            predicted_latent_dict[(test_uu,domain_testing)] = predicted_vector[inner_iid]
        except ValueError:
            predicted_latent_dict[(test_uu,domain_testing)] = -1000

predicted_latent = []
for index,row in pd_testing.iterrows():
    predicted_latent.append(predicted_latent_dict[(row['Users'],row['Domains'])])

pd_latent_results = pd.concat([pd_testing,pd.DataFrame(predicted_latent)],axis=1)
pd_latent_results.columns = ['Users','Domains','Ratings','Predicted']
pd_latent_results.to_csv('/home/saumya/Documents/USF/Project/ASD/recommendation_surprise/results_latent.csv',encoding='utf-8',index=False)

users_in_testing = pd_testing['Users'].unique()

pd_training_remove = pd_training.drop(pd_training[pd_training['Users'].isin(users_in_testing)].index)
users_in_training = pd_training_remove['Users'].unique()

data_latent = surprise.dataset.Dataset.load_from_df(pd_training_remove, reader)

algo_latent = surprise.SVD()
trainset_latent = data_latent.build_full_trainset()
algo_latent.fit(trainset_latent)

item_latent = algo_latent.qi

user_concept_vectors_training = {}

for (i,train_uu) in enumerate(users_in_training):
    if i%1000 == 0:
        print(i)
    pd_user_training = pd_training.loc[pd_training['Users'] == train_uu]
    user_vector = np.zeros(vector_len)
    for index,row in pd_user_training.iterrows():
        domain_user = row['Domains']
        rating_user = row['Ratings']
        try:
            inner_iid = trainset_latent.to_inner_iid(domain_user)
            user_vector[inner_iid] = rating_user
        except ValueError:
            continue
    concept_vector = np.matmul(user_vector,item_latent)
    user_concept_vectors_training[train_uu] = concept_vector

predicted_latent_2_dict = {}
neighborhood = 10

for (i,test_uu) in enumerate(users_in_testing):
    if i%100 == 0:
        print(i)
    pd_user_training = pd_training.loc[pd_training['Users'] == test_uu]
    user_vector = np.zeros(vector_len)
    for index,row in pd_user_training.iterrows():
        domain_user = row['Domains']
        rating_user = row['Ratings']
        try:
            inner_iid = trainset_latent.to_inner_iid(domain_user)
            user_vector[inner_iid] = rating_user
        except ValueError:
            continue
    concept_vector = np.matmul(user_vector,item_latent)
    similarity_dict = {}
    for train_uu in users_in_training:
        similarity_dict[train_uu] = cosine(user_concept_vectors_training[train_uu],concept_vector)
    most_similar_users = []
    for nn in range(neighborhood):
        user_v = max(similarity_dict.items(), key=operator.itemgetter(1))[0]
        most_similar_users.append(user_v)
        similarity_dict.pop(user_v)
    pd_user_testing = pd_testing.loc[pd_testing['Users'] == test_uu]
    for index,row in pd_user_testing.iterrows():
        domain_testing = row['Domains']
        try:
            inner_iid = trainset_latent.to_inner_iid(domain_testing)
            predicted_value = 0.0
            num_similar_users = 0
            for sim_user in most_similar_users:
                inner_uid = trainset_latent.to_inner_uid(sim_user)
                predicted_value = predicted_value + algo_latent.predict(uid=sim_user, iid=domain_testing).est
                num_similar_users = num_similar_users + 1
            predicted_latent_2_dict[(test_uu,domain_testing)] = predicted_value/num_similar_users
        except ValueError:
            predicted_latent_2_dict[(test_uu,domain_testing)] = -1000

predicted_latent_2 = []
for index,row in pd_testing.iterrows():
    predicted_latent_2.append(predicted_latent_2_dict[(row['Users'],row['Domains'])])

pd_latent_2_results = pd.concat([pd_testing,pd.DataFrame(predicted_latent_2)],axis=1)
pd_latent_2_results.columns = ['Users','Domains','Ratings','Predicted']
pd_latent_2_results.to_csv('/home/saumya/Documents/USF/Project/ASD/recommendation_surprise/results_latent_2_short.csv',encoding='utf-8',index=False)