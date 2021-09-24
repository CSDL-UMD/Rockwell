#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 13:34:45 2021

@author: saumya
"""

import requests
import os
import json
import time

def auth():
    cred = {}
    with open('credentials_v2', 'r') as f:
        for line in f.readlines():
            key, value = line.split(':')
            value = str.rstrip(value)
            cred[key] = value

    return cred['Bearer_token']

def create_url_following(user_id,pagination_token):
    if pagination_token:
        return "https://api.twitter.com/2/users/{}/following?max_results=1000&pagination_token={}".format(user_id,pagination_token)
    else:
        return "https://api.twitter.com/2/users/{}/following?max_results=1000".format(user_id)

def create_url_data(user_id,pagination_token):
    if pagination_token:
        return "https://api.twitter.com/2/users/{}/tweets?max_results=100&pagination_token={}".format(user_id,pagination_token)
    else:
        return "https://api.twitter.com/2/users/{}/tweets?max_results=100".format(user_id)

def get_params_following():
    # Tweet fields are adjustable.
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    return {}
        
def get_params():
    # Tweet fields are adjustable.
    # Options include:
    # attachments, author_id, context_annotations,
    # conversation_id, created_at, entities, geo, id,
    # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
    # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
    # source, text, and withheld
    return {"tweet.fields": "attachments,author_id,context_annotations,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,lang,possibly_sensitive,public_metrics,referenced_tweets,reply_settings,source,text,withheld"}


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def connect_to_endpoint(url, headers, params):
    response = requests.request("GET", url, headers=headers, params=params)
    #print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def main():
    user_id = 84653850
    num_pages_data = 5
    directory = "user_"+str(user_id)
    parent_dir = "/home/saumya/Documents/USF/Project/ASD/mock_social_media_platform/"
    path = os.path.join(parent_dir, directory)
    os.mkdir(path)
    bearer_token = auth()
    headers = create_headers(bearer_token)
    params_following = get_params_following()
    friends_id = []
    pagination_token = ""
    while(True):
        url = create_url_following(user_id,pagination_token)
        json_response = connect_to_endpoint(url, headers, params_following)
        response_data = json_response["data"]
        for i in range(len(response_data)):
            friends_id.append(int(response_data[i]["id"]))
        if "next_token" not in json_response["meta"].keys():
            break
        pagination_token = json_response["meta"]["next_token"]
    f = open(parent_dir+directory+"/friend_list.txt",'w')
    f.write(",".join([str(f_id) for f_id in friends_id]))
    f.close()
    print("Got Friends. Sleeping for 15 mins before starting data collection....")
    time.sleep(900)
    parent_dir_data = parent_dir + directory + "/"
    params_data = get_params()
    print("Number of Friends : "+str(len(friends_id)))
    requests_made = 0
    for i,friend in enumerate(friends_id):
        print("Collecting tweets of {} friend with id : {}".format(i,friend))
        directory_data = "friend_"+str(friends_id)
        path = os.path.join(parent_dir_data, directory_data)
        os.mkdir(path)
        pagination_token_data = ""
        for page in range(len(num_pages_data)):
            url = create_url_data(user_id,pagination_token_data)
            json_response = connect_to_endpoint(url, headers, params_data)
            response_data = json_response["data"]
            f = open(parent_dir_data+directory_data+"/page_"+str(page),'w')
            f.write(json.dumps(response_data, indent=4, sort_keys=True))
            f.close()
            requests_made = requests_made + 1
            if requests_made == 1500:
                print("Rate limit reached! Sleeping for 15 mins.....")
                time.sleep(900)
                requests_made = 0
            if "next_token" not in json_response["meta"].keys():
                break
            pagination_token = json_response["meta"]["next_token"]
    #url = create_url_data(user_id,"")
    #params = get_params()
    #json_response = connect_to_endpoint(url, headers, params)
    #response_data = json_response["data"]
    #print(len(response_data))
    #json_response = connect_to_endpoint(url, headers, params)
    #print(len(json_response['data']))
    #print(json.dumps(json_response, indent=4, sort_keys=True))


if __name__ == "__main__":
    main()