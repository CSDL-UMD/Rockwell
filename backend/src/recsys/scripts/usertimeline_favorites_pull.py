import json
import requests
import logging
import glob
import os
import gzip
from configparser import ConfigParser
from requests_oauthlib import OAuth1Session
from argparse import ArgumentParser

LOG_FMT_DEFAULT='%(asctime)s:%(levelname)s:%(message)s'
LOG_PATH_DEFAULT="/home/rockwell/Rockwell/backend/src/cronjobs/engagement_cronjob.log"

timeline_params = {
    "tweet.fields" : "id,text,edit_history_tweet_ids,attachments,author_id,conversation_id,created_at,entities,in_reply_to_user_id,lang,public_metrics,referenced_tweets,reply_settings",
    "user.fields" : "id,name,username,created_at,description,entities,location,pinned_tweet_id,profile_image_url,protected,public_metrics,url,verified",
    "media.fields": "media_key,type,url,duration_ms,height,preview_image_url,public_metrics,width",
    "expansions" : "author_id,referenced_tweets.id,attachments.media_keys",
}

def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db

def make_parser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", help="directory with data files")
    parser.add_argument("collection_count_usertimeline", help="How many user timeline tweets to collect")
    parser.add_argument("collection_count_favorites", help="How many favotrite tweets to collect")
    return parser

def createlookups(v2tweetobj,includenext=True,onlyincludequote=False):
    tweet_lookup = {}
    media_lookup = {}
    user_lookup = {}
    next_level_ids = []

    if "data" in v2tweetobj.keys():
        for v2tweet in v2tweetobj["data"]:
            tweet_lookup[v2tweet["id"]] = v2tweet
            if includenext:
                if "referenced_tweets" in v2tweet.keys():
                    for referenced_tweet in v2tweet["referenced_tweets"]: 
                        if referenced_tweet["type"] != "replied_to":
                            if onlyincludequote:
                                if referenced_tweet["type"] == "quoted":
                                    next_level_ids.append(referenced_tweet["id"])
                            else:
                                next_level_ids.append(referenced_tweet["id"])

    if "includes" in v2tweetobj.keys():
        if "media" in v2tweetobj["includes"].keys():
            for media_ele in v2tweetobj["includes"]["media"]:
                media_lookup[media_ele["media_key"]] = media_ele
        if "users" in v2tweetobj["includes"].keys():
            for user_ele in v2tweetobj["includes"]["users"]:
                user_lookup[user_ele["id"]] = user_ele

    return tweet_lookup,media_lookup,user_lookup,next_level_ids

def addallfields(v2tweet,v2user,v2media,v2tweetobj_user=None,v2tweetobj_fav=None):
    v1tweet = {}
    v1tweet["id"] = v2tweet["id"]
    v1tweet["id_str"] = v2tweet["id"]
    v1tweet["full_text"] = v2tweet["text"]
    v1tweet["favorite_count"] = v2tweet["public_metrics"]["like_count"]
    v1tweet["retweet_count"] = v2tweet["public_metrics"]["retweet_count"]
    v1tweet["created_at"] = v2tweet["created_at"]
    v1tweet["in_reply_to_status_id_str"] = ""
    v1tweet["favorited"] = False
    v1tweet["retweeted"] = False

    if "referenced_tweets" in v2tweet.keys():
        for referenced_tweet in v2tweet["referenced_tweets"]:
            if referenced_tweet["type"] == "replied_to":
                v1tweet["in_reply_to_status_id_str"] = referenced_tweet["id"]

    if v2tweetobj_user:
        if "data" in v2tweetobj_user.keys():
            for v2tweet_user in v2tweetobj_user["data"]:
                if "referenced_tweets" in v2tweet_user.keys():
                    for referenced_tweet in v2tweet_user["referenced_tweets"]:
                        if referenced_tweet["type"] == "retweeted":
                            if referenced_tweet["id"] == v2tweet["id"]:
                                v1tweet["retweeted"] = True

    if v2tweetobj_fav:
        if "data" in v2tweetobj_fav.keys():
            for v2tweet_fav in v2tweetobj_fav["data"]:
                if v2tweet_fav["id"] == v2tweet["id"]:
                    v1tweet["favorited"] = True


    v1tweet["user"] = {}
    v1tweet["user"]["name"] = v2user[v2tweet["author_id"]]["name"]
    v1tweet["user"]["profile_image_url"] = v2user[v2tweet["author_id"]]["profile_image_url"]
    v1tweet["user"]["screen_name"] = v2user[v2tweet["author_id"]]["username"]
    v1tweet["user"]["url"] = ""
    if "url" in v2user[v2tweet["author_id"]].keys():
        v1tweet["user"]["url"] = v2user[v2tweet["author_id"]]["url"]

    if "entities" in v2tweet.keys():
        if "urls" in v2tweet["entities"]:
            v1tweet["entities"] = {}
            v1tweet["entities"]["urls"] = []
            for v2_url in v2tweet["entities"]["urls"]:
                v1_url = {}
                v1_url["indices"] = [v2_url["start"],v2_url["end"]]
                v1_url["display_url"] = v2_url["display_url"]
                v1_url["expanded_url"] = v2_url["expanded_url"]
                v1_url["url"] = v2_url["url"]
                v1tweet["entities"]["urls"].append(v1_url)

    if "attachments" in v2tweet.keys():
        if "media_keys" in v2tweet["attachments"].keys():
            if "entities" not in v1tweet.keys():
                v1tweet["entities"] = {}
            v1tweet["entities"]["media"] = []
            for media_key in v2tweet["attachments"]["media_keys"]:
                v1_media = {}
                if "url" in v2media[media_key].keys():
                    v1_media["media_url"] = v2media[media_key]["url"]
                    v1_media["expanded_url"] = v2media[media_key]["url"]
                else:
                    v1_media["media_url"] = v2media[media_key]["preview_image_url"]
                    v1_media["expanded_url"] = v2media[media_key]["preview_image_url"]
                v1tweet["entities"]["media"].append(v1_media)

    return v1tweet

def convertv2tov1(v2tweetobj,cred,v2tweetobj_user=None,v2tweetobj_fav=None):

    oauth_new = OAuth1Session(cred['key'],
                    client_secret=cred['key_secret'],
                    resource_owner_key=cred['token'],
                    resource_owner_secret=cred['token_secret'])

    v1_tweets_all = []

    tweet_1_lookup = {}
    tweet_1_media_lookup = {}
    tweet_1_user_lookup = {}

    tweet_2_lookup = {}
    tweet_2_media_lookup = {}
    tweet_2_user_lookup = {}

    tweet_3_lookup = {}
    tweet_3_media_lookup = {}
    tweet_3_user_lookup = {}

    tweet_2_ids = []
    tweet_3_ids = []

    tweet_1_lookup,tweet_1_media_lookup,tweet_1_user_lookup,tweet_2_ids = createlookups(v2tweetobj)

    if tweet_2_ids:
        new_tweet_params = {
            "ids" : ",".join(tweet_2_ids),
            "tweet.fields" : timeline_params["tweet.fields"],
            "user.fields" : timeline_params["user.fields"],
            "media.fields" : timeline_params["media.fields"],
            "expansions" : timeline_params["expansions"],
        }
        response_tweet_2 = oauth_new.get("https://api.twitter.com/2/tweets", params=new_tweet_params)
        v2tweetobj_2 = json.loads(response_tweet_2.text)
        tweet_2_lookup,tweet_2_media_lookup,tweet_2_user_lookup,tweet_3_ids = createlookups(v2tweetobj_2,onlyincludequote=True)

    if tweet_3_ids:
        new_tweet_params = {
            "ids" : ",".join(tweet_3_ids),
            "tweet.fields" : timeline_params["tweet.fields"],
            "user.fields" : timeline_params["user.fields"],
            "media.fields" : timeline_params["media.fields"],
            "expansions" : timeline_params["expansions"],
        }
        response_tweet_3 = oauth_new.get("https://api.twitter.com/2/tweets", params=new_tweet_params)
        v2tweetobj_3 = json.loads(response_tweet_3.text)
        tweet_3_lookup,tweet_3_media_lookup,tweet_3_user_lookup,no_matter_ids = createlookups(v2tweetobj_3,includenext=False)

    if "data" in v2tweetobj.keys():
        for v2tweet in v2tweetobj["data"]:
            v1tweet = addallfields(v2tweet,tweet_1_user_lookup,tweet_1_media_lookup,v2tweetobj_user=v2tweetobj_user,v2tweetobj_fav=v2tweetobj_fav)
            if "referenced_tweets" in v2tweet.keys():
                for referenced_tweet in v2tweet["referenced_tweets"]:
                    if referenced_tweet["type"] == "retweeted":
                        v2tweet_retweeted = tweet_2_lookup[referenced_tweet["id"]]
                        v1tweet["retweeted_status"] = addallfields(v2tweet_retweeted,tweet_2_user_lookup,tweet_2_media_lookup)
                        if "referenced_tweets" in v2tweet_retweeted.keys():
                            for double_referenced_tweet in v2tweet_retweeted["referenced_tweets"]:
                                if double_referenced_tweet["type"] == "quoted":
                                    v2tweet_retweeted_quoted = tweet_3_lookup[double_referenced_tweet["id"]]
                                    v1tweet["retweeted_status"]["quoted_status"] = addallfields(v2tweet_retweeted_quoted,tweet_3_user_lookup,tweet_3_media_lookup)
                    if referenced_tweet["type"] == "quoted":
                        v2tweet_quoted = tweet_2_lookup[referenced_tweet["id"]]
                        v1tweet["quoted_status"] = addallfields(v2tweet_quoted,tweet_2_user_lookup,tweet_2_media_lookup)
            v1_tweets_all.append(v1tweet)

    return v1_tweets_all

def main(data_dir, collection_count_usertimeline, collection_count_favorites):
    print("One time usertimeline and favotes pull started")
    try:
        cred = config('../../configuration/config.ini','twitterapp')
    except Exception as e:
        print(e)
        print("Problem getting Twitter keys from Configuration")
        return
    data_dir = os.path.abspath(data_dir)
    curr_dir = os.getcwd()
    try:
        os.chdir(data_dir)
        hometimeline_files = sorted(glob.glob("*_home_*.json.gz"))
        for filee in hometimeline_files:
        	path = os.path.join(data_dir, filee)
        	with gzip.open(path, 'r') as fin:
        		data = json.loads(fin.read().decode('utf-8'))
        		access_token = data['accessToken']
        		access_token_secret = data['accessTokenSecret']
        		user_id = data['userObject']['twitter_id']
        		cred['token'] = access_token.strip()
        		cred['token_secret'] = access_token_secret.strip()
        		oauth = OAuth1Session(cred['key'],
                        client_secret=cred['key_secret'],
                        resource_owner_key=cred['token'],
                        resource_owner_secret=cred['token_secret'])
        		timeline_params_usertimeline = timeline_params
        		timeline_params_usertimeline['max_results'] = collection_count_usertimeline
        		response = oauth.get("https://api.twitter.com/2/users/{}/tweets".format(user_id), params = timeline_params_usertimeline)
        		v2tweetobj = json.loads(response.text)
        		if "data" not in v2tweetobj.keys():
        			print("No usertimeline data for : "+str(data['userObject']['screen_name']))
        			print(response.text)
        		else:
        			v1tweetobj = convertv2tov1(v2tweetobj,cred)
        			writeObj = {
        				"MTurkId" : data['MTurkId'],
        				"MTurkHitId" : data['MTurkHitId'],
        				"MTurkAssignmentId" : data['MTurkAssignmentId'],
        				"accessToken": data['accessToken'],
        				"accessTokenSecret": data['accessTokenSecret'],
        				"worker_id": data['worker_id'],
        				"userObject": data['userObject'],
        				"userTweets" : v1tweetobj,
        				"userTweetsv2" : v2tweetobj
        			}
        			with gzip.open("../../authorizer/usertimeline_data/{}_user.json.gz".format(user_id),"w") as outfile:
        				outfile.write(json.dumps(writeObj).encode('utf-8'))
        		timeline_params_favorites = timeline_params
        		timeline_params_favorites['max_results'] = collection_count_favorites
        		response = oauth.get("https://api.twitter.com/2/users/{}/liked_tweets".format(user_id), params = timeline_params_favorites)
        		v2tweetobj = json.loads(response.text)
        		if "data" not in v2tweetobj.keys():
        			print("No favorites data for : "+str(data['userObject']['screen_name']))
        			print(response.text)
        		else:
        			v1tweetobj = convertv2tov1(v2tweetobj,cred)
        			writeObj = {
        				"MTurkId" : data['MTurkId'],
        				"MTurkHitId" : data['MTurkHitId'],
        				"MTurkAssignmentId" : data['MTurkAssignmentId'],
        				"accessToken": data['accessToken'],
        				"accessTokenSecret": data['accessTokenSecret'],
        				"worker_id": data['worker_id'],
        				"userObject": data['userObject'],
        				"favTweets" : v1tweetobj,
        				"favTweetsv2" : v2tweetobj
        			}
        			with gzip.open("../../authorizer/favorites_data/{}_fav.json.gz".format(user_id),"w") as outfile:
        				outfile.write(json.dumps(writeObj).encode('utf-8'))
        os.chdir(curr_dir)
        return
    except Exception as e:
        print(e)
    finally:
        os.chdir(curr_dir)
        return

if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    main(args.data_dir,args.collection_count_usertimeline,args.collection_count_favorites)
