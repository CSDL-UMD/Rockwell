#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 03:44:42 2021

@author: saumyabhadani
"""

from collections import defaultdict

data_path = "/home/saumyabhadani/Downloads/RecSys/"

all_features = ["text_ tokens", "hashtags", "tweet_id", "present_media", "present_links", "present_domains",\
                "tweet_type","language", "tweet_timestamp", "engaged_with_user_id", "engaged_with_user_follower_count",\
               "engaged_with_user_following_count", "engaged_with_user_is_verified", "engaged_with_user_account_creation",\
               "enaging_user_id", "enaging_user_follower_count", "enaging_user_following_count", "enaging_user_is_verified",\
               "enaging_user_account_creation", "engagee_follows_engager"]

all_features_to_idx = dict(zip(all_features, range(len(all_features))))
labels_to_idx = {"retweet_timestamp": 21, "retweet_with_comment_timestamp": 22, "like_timestamp": 23}

users = []
domains = []
user_domains_map = defaultdict(int)

file_numbers = ["00","01","02","03","04","05","06","07","08","09","10","11","12"]

for file_num in file_numbers:
    print(file_num)
    f = open(data_path+"training_10M-"+file_num+".tsv", encoding="utf-8")
    lines = f.readlines()
    print("Total lines : "+str(len(lines)))
    for (i,line) in enumerate(lines):
        if i%1000 == 0:
            print(i)
        line = line.strip()
        features = line.split("\x01")
        domain_list = features[all_features_to_idx['present_domains']]
        engaging_user = features[all_features_to_idx['enaging_user_id']]
        if domain_list:
            domains = domain_list.split("\t")
            reaction = False
            for label, idx in labels_to_idx.items():
                if features[idx]:
                    reaction = True
            if reaction:
                users.append(engaging_user)
                for domain in domains:
                    domains.append(domain)
                    user_domains_map[(engaging_user,domain_list)] = user_domains_map[(engaging_user,domain_list)] + 1
                    