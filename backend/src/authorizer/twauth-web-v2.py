import os
import re
import gzip
import html
import numpy as np
from dateutil import parser
from flask import Flask, render_template, request, url_for, redirect, flash, make_response, jsonify
import requests
import random, string
import datetime
from requests_oauthlib import OAuth1Session
#from src.databaseAccess.database_config import config
from configparser import ConfigParser
from collections import defaultdict
import src.feedGeneration.CardInfo as CardInfo
import logging
import json
import glob
import xml
import xml.sax.saxutils

app = Flask(__name__)

app.debug = True

#log_level = logging.DEBUG
#logging.basicConfig(filename='authorizer.log', level=log_level)

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


webInformation = config('../configuration/config.ini','webconfiguration')

app_callback_url = str(webInformation['callback'])
app_callback_url_qual = str(webInformation['qualcallbackv2'])
request_token_url = str(webInformation['request_token_url'])
access_token_url = str(webInformation['access_token_url'])
authorize_url = str(webInformation['authorize_url'])
rockwell_url = str(webInformation['app_route'])
account_settings_url = str(webInformation['account_settings_url'])

timeline_params = {
    "tweet.fields" : "id,text,edit_history_tweet_ids,attachments,author_id,conversation_id,created_at,entities,in_reply_to_user_id,lang,public_metrics,referenced_tweets,reply_settings",
    "user.fields" : "id,name,username,created_at,description,entities,location,pinned_tweet_id,profile_image_url,protected,public_metrics,url,verified",
    "media.fields": "media_key,type,url,duration_ms,height,preview_image_url,public_metrics,width",
    "expansions" : "author_id,referenced_tweets.id,attachments.media_keys"
}

oauth_store = {}
start_url_store = {}
screenname_store = {}
userid_store = {}
worker_id_store = {}
access_token_store = {}
access_token_secret_store = {}
max_page_store = {}
session_id_store = {}
twitterversion_store = {}
mode_store = {}
participant_id_store = {}
assignment_id_store = {}
project_id_store = {}
completed_survey = {}

def filter_tweets(feedtweetsv1,feedtweetsv2):
    level_1_tweets = []
    level_2_retweeted = []
    filtered_feedtweets = []
    filtered_feedtweetsv2 = []
    for (i,tweet) in enumerate(feedtweetsv1):
        unique = False
        no_reply = True
        if tweet["id_str"] not in level_1_tweets:
            if "retweeted_status" in tweet.keys():
                if tweet["retweeted_status"]["id_str"] not in level_1_tweets and tweet["retweeted_status"]["id_str"] not in level_2_retweeted:
                    level_1_tweets.append(tweet["id_str"])
                    level_2_retweeted.append(tweet["retweeted_status"]["id_str"])
                    unique = True
            else:
                level_1_tweets.append(tweet["id_str"])
                unique = True
        if tweet["in_reply_to_status_id_str"]:
            reply = False
        if unique and no_reply:
            filtered_feedtweets.append(tweet)
            filtered_feedtweetsv2.append(feedtweetsv2[i])
    return filtered_feedtweets,filtered_feedtweetsv2

def break_timeline_attention(public_tweets,public_tweets_score,absent_tweets,max_pages):
    db_tweet_payload = []
    db_tweet_attn_payload = []
    absent_tweets_ids = []
    rankk = 0
    tweetids_by_page = defaultdict(list)
    print(absent_tweets)
    all_tweet_ids = [tweet['id'] for tweet in public_tweets if type(tweet) != float]
    for (i,tweet) in enumerate(public_tweets):
        if type(tweet) == float:
                continue
        page = int(rankk/10)
        rank_in_page = (rankk%10) + 1
        db_tweet = {
            'fav_before':str(tweet['favorited']),
            'tid':str(tweet["id"]),
            'rtbefore':str(tweet['retweeted']),
            'page':page,
            'rank':rank_in_page,
            'predicted_score':public_tweets_score[i]
        }
        db_tweet_payload.append(db_tweet)
        tweetids_by_page[page].append(tweet["id"])
        rankk = rankk + 1

    for tweet in absent_tweets:
        if type(tweet) == float:
                continue
        absent_tweets_ids.append(tweet["id_str"])

    for attn_page in range(max_pages):
        present_tweets_ids = tweetids_by_page[attn_page]
        present_tweets_select = np.random.choice(present_tweets_ids,size=3,replace=False)
        absent_tweets_select = np.random.choice(absent_tweets_ids,size=2,replace=False)
        for absent_tweet_id in absent_tweets_select:
            absent_tweets_ids.remove(absent_tweet_id)
        all_attn_tweets = np.concatenate((present_tweets_select,absent_tweets_select),axis=0)
        np.random.shuffle(all_attn_tweets)
        for (attn_rank,tt) in enumerate(all_attn_tweets):
            present = False
            if tt in present_tweets_select:
                present = True
            db_tweet_attn = {
                'tweet_id':str(tt),
                'page':str(attn_page),
                'rank':str(attn_rank),
                'present':present
            }
            db_tweet_attn_payload.append(db_tweet_attn)
    return db_tweet_payload,db_tweet_attn_payload

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


@app.route('/auth/')
def start():
    cred = config('../configuration/config.ini','twitterapp')

    try:
        request_token = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'])
        content = request_token.post(request_token_url, data = {"oauth_callback":app_callback_url})
        logging.info('Twitter access successfull')
    except Exception as error:
        print('Twitter access failed with error : '+str(error))
        logging.error('Twitter access failed with error : '+str(error))

    #request_token = dict(urllib.parse.parse_qsl(content))
    #oauth_token = request_token[b'oauth_token'].decode('utf-8')
    #oauth_token_secret = request_token[b'oauth_token_secret'].decode('utf-8')

    data_tokens = content.text.split("&")

    oauth_token = data_tokens[0].split("=")[1]
    oauth_token_secret = data_tokens[1].split("=")[1]
    oauth_store[oauth_token] = oauth_token_secret
    start_url = authorize_url+"?oauth_token="+oauth_token
    #res = make_response(render_template('index.html', authorize_url=authorize_url, oauth_token=oauth_token, request_token_url=request_token_url))
    res = make_response(render_template('YouGov.html', start_url=start_url, screenname="###", rockwell_url="###"))
    # Trying to add a browser cookie
    #res.set_cookie('exp','infodiversity',max_age=1800)
    return res
    #return render_template('index.html', authorize_url=authorize_url, oauth_token=oauth_token, request_token_url=request_token_url)

@app.route('/qualauth/')
def qualstart():
    cred = config('../configuration/config.ini','twitterapp')

    try:
        request_token = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'])
        content = request_token.post(request_token_url, data = {"oauth_callback":app_callback_url_qual})
        logging.info('Twitter access successfull')
    except Exception as error:
        print('Twitter access failed with error : '+str(error))
        logging.error('Twitter access failed with error : '+str(error))

    #request_token = dict(urllib.parse.parse_qsl(content))
    #oauth_token = request_token[b'oauth_token'].decode('utf-8')
    #oauth_token_secret = request_token[b'oauth_token_secret'].decode('utf-8')

    data_tokens = content.text.split("&")

    oauth_token = data_tokens[0].split("=")[1]
    oauth_token_secret = data_tokens[1].split("=")[1] 
    oauth_store[oauth_token] = oauth_token_secret
    screenname_store[oauth_token] = "####"
    start_url = authorize_url+"?oauth_token="+oauth_token
    start_url_store[oauth_token] = start_url
    #res = make_response(render_template('YouGovQualtrics.html', start="Yes", start_url=start_url))
    #return res
    return oauth_token
    #res = make_response(render_template('index.html', authorize_url=authorize_url, oauth_token=oauth_token, request_token_url=request_token_url))
    #res = make_response(render_template('YouGov.html', start_url=start_url, screenname="###", rockwell_url="###"))
    # Trying to add a browser cookie
    #res.set_cookie('exp','infodiversity',max_age=1800)
    #return res
    #return render_template('index.html', authorize_url=authorize_url, oauth_token=oauth_token, request_token_url=request_token_url)

@app.route('/qualrender')
def qualrender():
    oauth_token_qualtrics = request.args.get('oauth_token')
    mode = request.args.get('mode').strip()
    participant_id = request.args.get('participant_id').strip()
    assignment_id = request.args.get('assignment_id').strip()
    project_id = request.args.get('project_id').strip()
    mode_store[oauth_token_qualtrics] = mode
    participant_id_store[oauth_token_qualtrics] = participant_id
    assignment_id_store[oauth_token_qualtrics] = assignment_id
    project_id_store[oauth_token_qualtrics] = project_id
    start_url = start_url_store[oauth_token_qualtrics]
    res = make_response(render_template('YouGovQualtrics.html', start="Yes", start_url=start_url, oauth_token=oauth_token_qualtrics, mode=mode ,secretidentifier="_rockwellidentifierv2_", insertfeedurl=webInformation['url']+"/insertfeedqualtrics"))
    return res

@app.route('/callback')
def callback():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    oauth_denied = request.args.get('denied')

    if oauth_denied:
        if oauth_denied in oauth_store:
            del oauth_store[oauth_denied]
        #return render_template('error.html', error_message="the OAuth request was denied by this user")
        return redirect('http://' + str(webInformation['url']))

    if not oauth_token or not oauth_verifier:
        return render_template('error.html', error_message="callback param(s) missing")

    # unless oauth_token is still stored locally, return error
    if oauth_token not in oauth_store:
        return render_template('error.html', error_message="oauth_token not found locally")

    oauth_token_secret = oauth_store[oauth_token]

    # if we got this far, we have both callback params and we have
    # found this token locally

    #consumer = oauth.Consumer(
    #    app.config['APP_CONSUMER_KEY'], app.config['APP_CONSUMER_SECRET'])
    #token = oauth.Token(oauth_token, oauth_token_secret)
    #token.set_verifier(oauth_verifier)
    #client = oauth.Client(consumer, token)

    #resp, content = client.request(access_token_url, "POST")
    
    cred = config('../configuration/config.ini','twitterapp')
    oauth_access_tokens = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'],resource_owner_key=oauth_token,resource_owner_secret=oauth_token_secret,verifier=oauth_verifier)
    content = oauth_access_tokens.post(access_token_url)  

    #access_token = dict(urllib.parse.parse_qsl(content))

    access_token = content.text.split("&")

    # These are the tokens you would store long term, someplace safe
    real_oauth_token = access_token[0].split("=")[1]
    real_oauth_token_secret = access_token[1].split("=")[1]
    user_id = access_token[2].split("=")[1]
    screen_name = access_token[3].split("=")[1]

    oauth_account_settings = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'],resource_owner_key=real_oauth_token,resource_owner_secret=real_oauth_token_secret)
    response = oauth_account_settings.get(account_settings_url)
    account_settings_user = json.dumps(json.loads(response.text))

    insert_user_payload = {'twitter_id': str(user_id), 'account_settings': account_settings_user}
    resp_worker_id = requests.get('http://' + webInformation['localhost'] + ':5052/insert_user',params=insert_user_payload)
    worker_id = resp_worker_id.json()["data"]

    attn = 0
    page = 0
    pre_attn_check = 1

    random_identifier_len = random.randint(15, 26)   
    random_identifier = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random_identifier_len))
    set_user_credentials_payload_db = {'worker_id': str(worker_id), 'random_indentifier': random_identifier}
    set_user_credentials_payload = {'access_token': str(real_oauth_token), 'access_token_secret': str(real_oauth_token_secret), 'screen_name': str(screen_name), 'user_id': str(user_id), 'worker_id': str(worker_id), 'random_indentifier': random_identifier}
    requests.post('http://' + webInformation['localhost'] + ':5052/set_credentials',params=set_user_credentials_payload_db)
    requests.post('http://' + webInformation['localhost'] + ':5051/set_credentials',params=set_user_credentials_payload)


    #rockwell_url_agg = str(webInformation['app_route']) + '?access_token=' + str(real_oauth_token) + '&access_token_secret=' + str(real_oauth_token_secret) + '&user_id=' + str(user_id) + '&screen_name=' + str(screen_name) + '&worker_id=' + str(worker_id) + '&attn=' + str(attn) + '&page=' + str(page)
    rockwell_url_agg = str(webInformation['app_route']) + '?randomtokenszzzz=' + random_identifier + '&attn=' + str(attn) + '&page=' + str(page) 
    #rockwell_url_agg = 'http://127.0.0.1:3000' + '?access_token=' + str(real_oauth_token) + '&access_token_secret=' + str(real_oauth_token_secret) + '&worker_id=' + str(worker_id) + '&attn=' + str(attn) + '&page=' + str(page) + '&pre_attn_check=' + str(pre_attn_check)

    del oauth_store[oauth_token]
    #redirect(rockwell_url + '?access_token=' + real_oauth_token + '&access_token_secret=' + real_oauth_token_secret)


    #return render_template('placeholder.html', worker_id=worker_id, access_token=real_oauth_token, access_token_secret=real_oauth_token_secret)
    return render_template('YouGov.html', start_url="###", screenname=screen_name, rockwell_url=rockwell_url_agg)

@app.route('/qualcallback')
def qualcallback():
    print("CALLBACK CALLED!!!!")
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    oauth_denied = request.args.get('denied')


    if oauth_denied:
        if oauth_denied in oauth_store:
            del oauth_store[oauth_denied]
        #screenname_store[oauth_token] = "#DENIED#"
        #return render_template('error.html', error_message="the OAuth request was denied by this user")
        #return redirect('http://' + str(webInformation['url']) + ':5000')
        return "<script>window.onload = window.close();</script>"

    #if not oauth_token or not oauth_verifier:
    #    return render_template('error.html', error_message="callback param(s) missing")

    # unless oauth_token is still stored locally, return error
    #if oauth_token not in oauth_store:
    #    return render_template('error.html', error_message="oauth_token not found locally")

    oauth_token_secret = oauth_store[oauth_token]

    # if we got this far, we have both callback params and we have
    # found this token locally

    #consumer = oauth.Consumer(
    #    app.config['APP_CONSUMER_KEY'], app.config['APP_CONSUMER_SECRET'])
    #token = oauth.Token(oauth_token, oauth_token_secret)
    #token.set_verifier(oauth_verifier)
    #client = oauth.Client(consumer, token)

    #resp, content = client.request(access_token_url, "POST")
    
    cred = config('../configuration/config.ini','twitterapp')
    oauth_access_tokens = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'],resource_owner_key=oauth_token,resource_owner_secret=oauth_token_secret,verifier=oauth_verifier)
    content = oauth_access_tokens.post(access_token_url)  

    #access_token = dict(urllib.parse.parse_qsl(content))

    access_token = content.text.split("&")

    # These are the tokens you would store long term, someplace safe
    real_oauth_token = access_token[0].split("=")[1]
    real_oauth_token_secret = access_token[1].split("=")[1]
    user_id = access_token[2].split("=")[1]
    screen_name = access_token[3].split("=")[1]

    oauth_account_settings = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'],resource_owner_key=real_oauth_token,resource_owner_secret=real_oauth_token_secret)
    response = oauth_account_settings.get(account_settings_url)
    account_settings_user = json.dumps(json.loads(response.text))

    mode = mode_store[oauth_token]
    mturk_ref_id = 1

    if mode == "ELIGIBILITY":
        participant_id = participant_id_store[oauth_token]
        assignment_id = assignment_id_store[oauth_token]
        project_id = project_id_store[oauth_token]
        insert_mturk_user_payload = {'participant_id': participant_id,'assignment_id': assignment_id, 'project_id': project_id}
        resp_mturk_ref_id = requests.get('http://' + webInformation['localhost'] + ':5052/insert_mturk_user',params=insert_mturk_user_payload)
        mturk_ref_id = resp_mturk_ref_id.json()["data"]

    worker_id = ''
    db_response_screenname = requests.get('http://127.0.0.1:5052/get_existing_tweets_new_screenname?screenname='+str(screenname)+"&page="+str(0)+"&feedtype=S")
    if db_response_screenname.json()['data'] == "NEW":
        worker_id = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
    else:
        worker_id = db_response_screenname.json()['data'][0][-1].strip()

    insert_user_payload = {'worker_id' : worker_id, 'mturk_ref_id' : mturk_ref_id, 'twitter_id': str(user_id),'access_token': real_oauth_token, 'access_token_secret': real_oauth_token_secret, 'screenname': screen_name, 'account_settings': account_settings_user}
    resp_worker_id = requests.get('http://' + webInformation['localhost'] + ':5052/insert_user',params=insert_user_payload)
    #worker_id = resp_worker_id.json()["data"]
    
    screenname_store[oauth_token] = screen_name
    userid_store[oauth_token] = user_id
    worker_id_store[oauth_token] = str(worker_id)
    access_token_store[oauth_token] = real_oauth_token
    access_token_secret_store[oauth_token] = real_oauth_token_secret
    completed_survey[worker_id] = False
    del oauth_store[oauth_token]

    res = make_response(render_template('YouGovQualtrics.html', start="No", worker_id=worker_id, oauth_token=oauth_token, mode=mode ,secretidentifier="_rockwellidentifierv2_", insertfeedurl=webInformation['url']+"/insertfeedqualtrics"))
    return res

    #return "<script>window.onload = window.close();</script>"
    #return "Done!!"
    
    #insert_user_payload = {'twitter_id': str(user_id), 'account_settings': account_settings_user}
    #resp_worker_id = requests.get('http://' + webInformation['url'] + ':5052/insert_user',params=insert_user_payload)
    #worker_id = resp_worker_id.json()["data"]

    #attn = 0
    #page = 0
    #pre_attn_check = 1

    #rockwell_url_agg = str(webInformation['app_route']) + '?access_token=' + str(real_oauth_token) + '&access_token_secret=' + str(real_oauth_token_secret) + '&worker_id=' + str(worker_id) + '&attn=' + str(attn) + '&page=' + str(page) 
    #rockwell_url_agg = 'http://127.0.0.1:3000' + '?access_token=' + str(real_oauth_token) + '&access_token_secret=' + str(real_oauth_token_secret) + '&worker_id=' + str(worker_id) + '&attn=' + str(attn) + '&page=' + str(page) + '&pre_attn_check=' + str(pre_attn_check)

    #redirect(rockwell_url + '?access_token=' + real_oauth_token + '&access_token_secret=' + real_oauth_token_secret)

    #return render_template('placeholder.html', worker_id=worker_id, access_token=real_oauth_token, access_token_secret=real_oauth_token_secret)
    #return render_template('YouGov.html', start_url="###", screenname=screen_name, rockwell_url=rockwell_url_agg)

@app.route('/insertfeedqualtrics', methods=['GET','POST'])
def insert_feed_qualtrics():
    worker_id = request.args.get('worker_id').strip()
    print("Worker ID in insertfeedqualtrics")
    print(worker_id)
    oauth_token = request.args.get('oauth_token')
    db_response = requests.get('http://127.0.0.1:5052/get_existing_user?worker_id='+str(worker_id))
    #print(db_response.json())
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    screenname = db_response[0][2]
    userid = db_response[0][3]
    db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page="+str(0)+"&feedtype=S")
    need_to_fetch_screenname = False
    need_to_fetch_tweets = False
    if db_response.json()['data'] == "NEW":
        need_to_fetch_screenname = True
    if need_to_fetch_screenname:
        db_response_screenname = requests.get('http://127.0.0.1:5052/get_existing_tweets_new_screenname?screenname='+str(screenname)+"&page="+str(0)+"&feedtype=S")
        if db_response_screenname.json()['data'] == "NEW":
            need_to_fetch_tweets = True
        else:
            worker_id = db_response_screenname.json()['data'][0][-1].strip()
    screenname_store[oauth_token] = screenname
    userid_store[oauth_token] = userid
    worker_id_store[oauth_token] = str(worker_id)
    access_token_store[oauth_token] = access_token
    access_token_secret_store[oauth_token] = access_token_secret
    completed_survey[worker_id] = False
    return worker_id

@app.route('/insertfeedqualtrics_prev', methods=['GET','POST'])
def insert_feed_qualtrics_prev():
    print("Called!!!")
    worker_id = request.args.get('worker_id').strip()
    oauth_token = request.args.get('oauth_token')
    db_response = requests.get('http://127.0.0.1:5052/get_existing_user?worker_id='+str(worker_id))
    #print(db_response.json())
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    screenname = db_response[0][2]
    userid = db_response[0][3]
    db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page="+str(0)+"&feedtype=S")
    need_to_fetch_screenname = False
    need_to_fetch_tweets = False
    if db_response.json()['data'] == "NEW":
        need_to_fetch_screenname = True
    else:
        last_updated_date_str = db_response.json()['data'][0][1]
        last_updated_date = datetime.datetime.strptime(last_updated_date_str,'%Y-%m-%d %H:%M:%S')
        datetime_now = datetime.datetime.now()
        diff = datetime_now - last_updated_date
        days, seconds = diff.days, diff.seconds
        hours = days * 24 + seconds // 3600
        if hours > 24:
            need_to_fetch_screenname = True
    if need_to_fetch_screenname:
        db_response_screenname = requests.get('http://127.0.0.1:5052/get_existing_tweets_new_screenname?screenname='+str(screenname)+"&page="+str(0)+"&feedtype=S")
        if db_response_screenname.json()['data'] == "NEW":
            need_to_fetch_tweets = True
        else:
            last_updated_date_str = db_response_screenname.json()['data'][0][1]
            last_updated_date = datetime.datetime.strptime(last_updated_date_str,'%Y-%m-%d %H:%M:%S')
            datetime_now = datetime.datetime.now()
            diff = datetime_now - last_updated_date
            days, seconds = diff.days, diff.seconds
            hours = days * 24 + seconds // 3600
            if hours > 24:
                need_to_fetch_tweets = True
            else:
                print("Yahan aaya????")
                worker_id = db_response_screenname.json()['data'][0][-1].strip()
                print(worker_id)
    if need_to_fetch_tweets:
        cred = config('../configuration/config.ini','twitterapp')
        cred['token'] = access_token.strip()
        cred['token_secret'] = access_token_secret.strip()
        oauth = OAuth1Session(cred['key'],
                            client_secret=cred['key_secret'],
                            resource_owner_key=cred['token'],
                            resource_owner_secret=cred['token_secret'])
        public_tweets = None
        refresh = 0
        new_session = True
        params = {"count": "60","tweet_mode": "extended"}
        #response = oauth.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params = params)
        response = oauth.get("https://api.twitter.com/2/users/{}/timelines/reverse_chronological".format(userid), params = timeline_params)
        if response.text == '{"errors":[{"code":89,"message":"Invalid or expired token."}]}':
            return "Invalid Token"
        if response.text == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
            print("Rate limit exceeded.")
        public_tweets = json.loads(response.text)
        #response_user = oauth.get("https://api.twitter.com/2/users/{}/tweets".format(userid), params = timeline_params)
        #response_fav = oauth.get("https://api.twitter.com/2/users/{}/liked_tweets".format(userid), params = timeline_params)
        public_tweets_user = json.loads(response_user.text)
        public_tweets_fav = json.loads(response_fav.text)
        public_tweets = convertv2tov1(public_tweets,cred,v2tweetobj_user=public_tweets_user,v2tweetobj_fav=public_tweets_fav)
        public_tweets = filter_tweets(public_tweets)
        if len(public_tweets) < 20:
            max_page_store[worker_id] == -1
        else:
            if len(public_tweets) > 60:
                public_tweets = public_tweets[0:60]
            db_tweet_payload = []
            for tweet in public_tweets:
                db_tweet = {
                    'tweet_id':tweet["id"],
                    'tweet_json':tweet
                }
                db_tweet_payload.append(db_tweet)
            public_tweets = public_tweets[0:len(public_tweets)-10]
            public_tweets_score = [-100]*len(public_tweets)
            absent_tweets = public_tweets[-10:]
            max_pages = int(len(public_tweets)/10)
            params_user = {"count": "200","tweet_mode": "extended"}
            #params_fav = {"count": "200", "user_id":user_id, "tweet_mode": "extended"}
            #response_user = oauth.get("https://api.twitter.com/1.1/statuses/user_timeline.json", params = params_user)
            #response_fav = oauth.get("https://api.twitter.com/1.1/statuses/favorites/list.json", params = params_user)
            #response_fav = oauth.get("https://api.twitter.com/2/users/"+str(user_id)+"/liked_tweets")
            #print("FAVORITES!!!!")
            #print(response_fav.text)
            public_tweets_user = convertv2tov1(public_tweets_user,cred)
            public_tweets_fav = convertv2tov1(public_tweets_fav,cred)
            #timeline_json = [public_tweets,public_tweets_user,public_tweets_fav]
            timeline_json = [public_tweets,public_tweets_user,screenname]
            recsys_response = requests.get('http://127.0.0.1:5053/recsys_rerank',json=timeline_json)
            public_tweets_control = recsys_response.json()['data'][0]
            public_tweets_control_score = recsys_response.json()['data'][1]
            db_tweet_chronological_payload,db_tweet_chronological_attn_payload = break_timeline_attention(public_tweets,public_tweets_score,absent_tweets,max_pages)
            db_tweet_control_payload,db_tweet_control_attn_payload = break_timeline_attention(public_tweets_control,public_tweets_control_score,absent_tweets,max_pages)
            finalJson = []
            finalJson.append(db_tweet_payload)
            finalJson.append(db_tweet_chronological_payload)
            finalJson.append(db_tweet_chronological_attn_payload)
            finalJson.append(db_tweet_control_payload)
            finalJson.append(db_tweet_control_attn_payload)
            finalJson.append(worker_id)
            finalJson.append(screenname)
            requests.post('http://127.0.0.1:5052/insert_timelines_attention',json=finalJson)
    screenname_store[oauth_token] = screenname
    userid_store[oauth_token] = userid
    worker_id_store[oauth_token] = str(worker_id)
    access_token_store[oauth_token] = access_token
    access_token_secret_store[oauth_token] = access_token_secret
    """
    if response.text == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
        print("Rate limit exceeded.")
    public_tweets = json.loads(response.text)
    if feedtype == "M":
        print("In M")
        timeline_json = [public_tweets,screen_name]
        recsys_response = requests.get('http://127.0.0.1:5054/recsys_rerank',json=timeline_json)
        public_tweets = recsys_response.json()['data']
    elif feedtype == "S":
        print("in S")
        params_user = {"count": "200","tweet_mode": "extended"}
        #params_fav = {"count": "200", "user_id":user_id, "tweet_mode": "extended"}
        response_user = oauth.get("https://api.twitter.com/1.1/statuses/user_timeline.json", params = params_user)
        response_fav = oauth.get("https://api.twitter.com/1.1/statuses/favorites/list.json", params = params_user)
        #response_fav = oauth.get("https://api.twitter.com/2/users/"+str(user_id)+"/liked_tweets")
        print("FAVORITES!!!!")
        print(response_fav.text)
        public_tweets_user = json.loads(response_user.text)
        #public_tweets_fav = json.loads(response_fav.text)
        #timeline_json = [public_tweets,public_tweets_user,public_tweets_fav]
        timeline_json = [public_tweets,public_tweets_user,screen_name]
        recsys_response = requests.get('http://127.0.0.1:5053/recsys_rerank',json=timeline_json)
        public_tweets = recsys_response.json()['data']
    tot_tweets = len(public_tweets)
    db_tweet_payload = []
    db_tweet_session_payload = []
    db_tweet_attn_payload = []
    rankk = 0
    tweetids_by_page = defaultdict(list)
    all_tweet_ids = [tweet['id'] for tweet in public_tweets]
    for tweet in public_tweets:
        page = int(rankk/10)
        rank_in_page = (rankk%10) + 1
        db_tweet = {
            'tweet_id':tweet["id"],
            'tweet_json':tweet
        }
        db_tweet_payload.append(db_tweet)
        db_tweet_session = {
            'fav_before':str(tweet['favorited']),
            'tid':str(tweet["id"]),
            'rtbefore':str(tweet['retweeted']),
            'page':page,
            'rank':rank_in_page
        }
        db_tweet_session_payload.append(db_tweet_session)
        tweetids_by_page[page].append(tweet["id"])
        rankk = rankk + 1
    for attn_page in range(3):
        present_tweets = tweetids_by_page[attn_page]
        absent_tweets = all_tweet_ids[(attn_page+1)*10+1:]
        present_tweets_select = np.random.choice(present_tweets,size=3,replace=False)
        absent_tweets_select = np.random.choice(absent_tweets,size=2,replace=False)
        all_attn_tweets = np.concatenate((present_tweets_select,absent_tweets_select),axis=0)
        np.random.shuffle(all_attn_tweets)
        for (attn_rank,tt) in enumerate(all_attn_tweets):
            present = False
            if tt in present_tweets_select:
                present = True
            db_tweet_attn = {
                'tweet_id':str(tt),
                'page':str(attn_page),
                'rank':str(attn_rank),
                'present':present
            }
            db_tweet_attn_payload.append(db_tweet_attn)
    finalJson = []
    finalJson.append(db_tweet_payload)
    finalJson.append(db_tweet_session_payload)
    finalJson.append(db_tweet_attn_payload)
    finalJson.append(worker_id)
    requests.post('http://127.0.0.1:5052/insert_tweet',json=finalJson)
    """
    return worker_id

@app.route('/auth/getscreenname')
def screenname():
    #print("GET SCEEN NAME CALLED!!!")
    oauth_token_qualtrics = request.args.get('oauth_token')
    screen_name_return = screenname_store[oauth_token_qualtrics]
    print("SCREEN NAME CALLED!!!!!!!!")
    print(screen_name_return)
    if screen_name_return == "####":
        return screen_name_return
    random_identifier_len = random.randint(15, 26)    
    random_identifier = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random_identifier_len))
    userid_return = userid_store[oauth_token_qualtrics]
    worker_id_return = worker_id_store[oauth_token_qualtrics]
    access_token_return = access_token_store[oauth_token_qualtrics]
    access_token_secret_return = access_token_secret_store[oauth_token_qualtrics]
    file_number = 1
    existing_home_timeline_files = sorted(glob.glob("UserData/{}_home_*.json.gz".format(userid_return)))
    if existing_home_timeline_files:
        latest_user_file = max(existing_home_timeline_files, key=lambda fn: int(fn.split(".")[0].split("_")[2]))
        file_number = int(latest_user_file.split(".")[0].split("_")[2]) + 1
    return screen_name_return+"$$$"+str(userid_return)+"$$$"+worker_id_return+"$$$"+access_token_return+"$$$"+access_token_secret_return+"$$$"+random_identifier+"$$$"+str(file_number)  

@app.route('/retweet_post', methods=['GET','POST'])
def retweet_post():
    worker_id = request.args.get('worker_id').strip()
    tweet_id = request.args.get('tweet_id').strip()
    db_response = requests.get('http://127.0.0.1:5052/get_existing_mturk_user?worker_id='+str(worker_id))
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    userid = db_response[0][3]

    cred = config('../configuration/config.ini','twitterapp')
    cred['token'] = access_token.strip()
    cred['token_secret'] = access_token_secret.strip()
    oauth = OAuth1Session(cred['key'],
                        client_secret=cred['key_secret'],
                        resource_owner_key=cred['token'],
                        resource_owner_secret=cred['token_secret'])

    try:
        payload = {"tweet_id" : tweet_id}
        response_retweet = oauth.post("https://api.twitter.com/2/users/{}/retweets".format(userid), json=payload)
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.route('/like_post', methods=['GET','POST'])
def like_post():
    worker_id = request.args.get('worker_id').strip()  
    tweet_id = request.args.get('tweet_id').strip()  
    db_response = requests.get('http://127.0.0.1:5052/get_existing_mturk_user?worker_id='+str(worker_id))
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    userid = db_response[0][3]

    cred = config('../configuration/config.ini','twitterapp')
    cred['token'] = access_token.strip()
    cred['token_secret'] = access_token_secret.strip()
    oauth = OAuth1Session(cred['key'],
                        client_secret=cred['key_secret'],
                        resource_owner_key=cred['token'],
                        resource_owner_secret=cred['token_secret'])

    try:
        payload = {"tweet_id" : tweet_id}
        response_likes = oauth.post("https://api.twitter.com/2/users/{}/likes".format(userid), json=payload)
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed


@app.route('/hometimeline', methods=['GET'])
def get_hometimeline():
    worker_id = request.args.get('worker_id').strip()
    file_number = request.args.get('file_number').strip()
    max_id = request.args.get('max_id').strip()
    collection_started = request.args.get('collection_started').strip()
    db_response = requests.get('http://127.0.0.1:5052/get_existing_mturk_user?worker_id='+str(worker_id))
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    screenname = db_response[0][2]
    userid = db_response[0][3]
    participant_id = db_response[0][4]
    assignment_id = db_response[0][5]
    project_id = db_response[0][6]
    v2tweetobj = {}
    v1tweetobj = {}

    errormessage = "NA"

    cred = config('../configuration/config.ini','twitterapp')
    cred['token'] = access_token.strip()
    cred['token_secret'] = access_token_secret.strip()
    oauth = OAuth1Session(cred['key'],
                        client_secret=cred['key_secret'],
                        resource_owner_key=cred['token'],
                        resource_owner_secret=cred['token_secret'])
    response = oauth.get("https://api.twitter.com/2/users/{}/timelines/reverse_chronological".format(userid), params = timeline_params)
    if response.text == '{"errors":[{"code":89,"message":"Invalid or expired token."}]}':
        errormessage = "Invalid Token"

    if response.text == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
        errormessage = "Rate Limit Exceeded"

    if errormessage == "NA":

        v2tweetobj_loaded = json.loads(response.text)

        if max_id != "INITIAL":
            for section in v2tweetobj_loaded.keys():
                if section == "data":
                    v2tweetobj["data"] = []
                    for v2tweet in v2tweetobj_loaded["data"]:
                        if int(v2tweet["id"]) > int(max_id):
                            v2tweetobj["data"].append(v2tweet)
                else:
                    v2tweetobj[section] = v2tweetobj_loaded[section]
        else:
            v2tweetobj = v2tweetobj_loaded

        v1tweetobj = convertv2tov1(v2tweetobj,cred)


    now_session_start = datetime.datetime.now()
    session_start = now_session_start.strftime('%Y-%m-%dT%H:%M:%S')

    collection_started_store = collection_started
    if collection_started == "INITIAL":
        collection_started_store = session_start

    newest_id = ""
    if "meta" in v2tweetobj.keys():
        newest_id = v2tweetobj["meta"]["newest_id"]

    userobj = {
        "screen_name" : screenname,
        "twitter_id" : userid
    }

    writeObj = {
        "MTurkId" : participant_id,
        "MTurkHitId" : assignment_id,
        "MTurkAssignmentId" : project_id,
        "collectionStarted" : collection_started_store,
        "timestamp" : session_start,
        "source": "pilot3",
        "accessToken": access_token,
        "accessTokenSecret": access_token_secret,
        "latestTweetId": newest_id,
        "worker_id": worker_id,
        "userObject": userobj,
        "homeTweets" : v1tweetobj,
        "errorMessage" : errormessage
    }

    with gzip.open("hometimeline_data/{}_home_{}.json.gz".format(userid,file_number),"w") as outfile:
        outfile.write(json.dumps(writeObj).encode('utf-8'))

    with gzip.open("UserDatav2/{}_home_{}.json.gz".format(userid,file_number),"w") as outfile:
        outfile.write(json.dumps(v2tweetobj).encode('utf-8'))

    feed_tweets,feed_tweets_v2 = filter_tweets(v1tweetobj,v2tweetobj)
    db_tweet_payload = []
    for (i,tweet) in enumerate(feed_tweets):
        db_tweet = {'tweet_id':tweet["id"],'tweet_json':tweet, 'tweet_json_v2':feed_tweets_v2[i]}
        db_tweet_payload.append(db_tweet)
    db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page=NA&feedtype=S")
    if db_response.json()['data'] != "NEW":
        existing_tweets = [response[6] for response in db_response.json()['data']]
        feed_tweets.extend(existing_tweets)
    feed_tweets = feed_tweets[0:len(feed_tweets)-10]
    absent_tweets = feed_tweets[-10:]
    feed_tweets_chronological = []
    feed_tweets_chronological_score = []
    for tweet in feed_tweets:
        feed_tweets_chronological.append(tweet)
        feed_tweets_chronological_score.append(-100)
    max_pages = min([len(feed_tweets),5])
    db_tweet_chronological_payload,db_tweet_chronological_attn_payload = break_timeline_attention(feed_tweets_chronological,feed_tweets_chronological_score,absent_tweets,max_pages)
    finalJson = []
    finalJson.append(db_tweet_payload)
    finalJson.append(db_tweet_chronological_payload)
    finalJson.append(db_tweet_chronological_attn_payload)
    finalJson.append(worker_id)
    finalJson.append(screenname)
    requests.post('http://127.0.0.1:5052/insert_timelines_attention_chronological',json=finalJson)

    #unprocessed_json = {}
    #with open("../configuration/unprocessed.json") as fin:
    #    unprocessed_json = json.loads(fin.read())
    #unprocessed_files = unprocessed_json["hometimeline"]
    #unprocessed_files.append(os.getcwd()+"/UserData/{}_home_{}.json.gz".format(userid,file_number))
    #unprocessed_files = list(set(unprocessed_files)) 
    #unprocessed_json["hometimeline"] = unprocessed_files
    #with open("../configuration/unprocessed.json","w") as outfile:
    #    outfile.write(json.dumps(unprocessed_json))

    return jsonify({"errorMessage" : errormessage})


@app.route('/usertimeline', methods=['GET'])
def get_usertimeline():
    worker_id = request.args.get('worker_id').strip()
    db_response = requests.get('http://127.0.0.1:5052/get_existing_mturk_user?worker_id='+str(worker_id))
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    screenname = db_response[0][2]
    userid = db_response[0][3]
    participant_id = db_response[0][4]
    assignment_id = db_response[0][5]
    project_id = db_response[0][6]
    v2tweetobj = {}
    v1tweetobj = {}

    errormessage = "NA"

    cred = config('../configuration/config.ini','twitterapp')
    cred['token'] = access_token.strip()
    cred['token_secret'] = access_token_secret.strip()
    oauth = OAuth1Session(cred['key'],
                        client_secret=cred['key_secret'],
                        resource_owner_key=cred['token'],
                        resource_owner_secret=cred['token_secret'])
    response = oauth.get("https://api.twitter.com/2/users/{}/tweets".format(userid), params = timeline_params)
    if response.text == '{"errors":[{"code":89,"message":"Invalid or expired token."}]}':
        errormessage = "Invalid Token"

    if response.text == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
        errormessage = "Rate Limit Exceeded"

    if errormessage == "NA":
        v2tweetobj = json.loads(response.text)
        v1tweetobj = convertv2tov1(v2tweetobj,cred)[0]

    newest_id = ""
    if "meta" in v2tweetobj.keys():
        newest_id = v2tweetobj["meta"]["newest_id"]

    userobj = {
        "screen_name" : screenname,
        "twitter_id" : userid
    }

    now_session_start = datetime.datetime.now()
    session_start = now_session_start.strftime('%Y-%m-%dT%H:%M:%S')

    writeObj = {
        "MTurkId" : participant_id,
        "MTurkHitId" : assignment_id,
        "MTurkAssignmentId" : project_id,
        "timestamp" : session_start,
        "source": "pilot3",
        "accessToken": access_token,
        "accessTokenSecret": access_token_secret,
        "latestTweetId": newest_id,
        "worker_id": worker_id,
        "userObject": userobj,
        "userTweets" : v1tweetobj,
        "errorMessage" : errormessage
    }

    with gzip.open("usertimeline_data/{}_user.json.gz".format(userid),"w") as outfile:
        outfile.write(json.dumps(writeObj).encode('utf-8'))

    with gzip.open("UserDatav2/{}_user.json.gz".format(userid),"w") as outfile:
        outfile.write(json.dumps(v2tweetobj).encode('utf-8'))

    return jsonify({"errorMessage" : errormessage})


@app.route('/favorites', methods=['GET'])
def get_favorites():
    worker_id = request.args.get('worker_id').strip()
    db_response = requests.get('http://127.0.0.1:5052/get_existing_mturk_user?worker_id='+str(worker_id))
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    screenname = db_response[0][2]
    userid = db_response[0][3]
    participant_id = db_response[0][4]
    assignment_id = db_response[0][5]
    project_id = db_response[0][6]
    v2tweetobj = {}
    v1tweetobj = {}

    errormessage = "NA"

    cred = config('../configuration/config.ini','twitterapp')
    cred['token'] = access_token.strip()
    cred['token_secret'] = access_token_secret.strip()
    oauth = OAuth1Session(cred['key'],
                        client_secret=cred['key_secret'],
                        resource_owner_key=cred['token'],
                        resource_owner_secret=cred['token_secret'])
    response = oauth.get("https://api.twitter.com/2/users/{}/liked_tweets".format(userid), params = timeline_params)
    if response.text == '{"errors":[{"code":89,"message":"Invalid or expired token."}]}':
        errormessage = "Invalid Token"

    if response.text == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
        errormessage = "Rate Limit Exceeded"

    if errormessage == "NA":
        v2tweetobj = json.loads(response.text)
        v1tweetobj = convertv2tov1(v2tweetobj,cred)[0]

    newest_id = ""
    #if "meta" in v2tweetobj.keys():
    #    newest_id = v2tweetobj["meta"]["newest_id"]

    userobj = {
        "screen_name" : screenname,
        "twitter_id" : userid
    }

    now_session_start = datetime.datetime.now()
    session_start = now_session_start.strftime('%Y-%m-%dT%H:%M:%S')

    writeObj = {
        "MTurkId" : participant_id,
        "MTurkHitId" : assignment_id,
        "MTurkAssignmentId" : project_id,
        "timestamp" : session_start,
        "source": "pilot3",
        "accessToken": access_token,
        "accessTokenSecret": access_token_secret,
        "latestTweetId": newest_id,
        "worker_id": worker_id,
        "userObject": userobj,
        "likedTweets" : v1tweetobj,
        "errorMessage" : errormessage
    }

    with gzip.open("favorites_data/{}_fav.json.gz".format(userid),"w") as outfile:
        outfile.write(json.dumps(writeObj).encode('utf-8'))

    with gzip.open("UserDatav2/{}_fav.json.gz".format(userid),"w") as outfile:
        outfile.write(json.dumps(v2tweetobj).encode('utf-8'))

    return jsonify({"errorMessage" : errormessage})


@app.route('/getfeed', methods=['GET'])
def get_feed():
    worker_id = str(request.args.get('worker_id')).strip()
    print("WORKER ID IN GET FEED!!!")
    print(worker_id)
    attn = int(request.args.get('attn'))
    page = int(request.args.get('page'))
    feedtype = str(request.args.get('feedtype')).strip()
    session_id = -1
    if attn == 0 and page == 0:
        insert_session_payload = {'worker_id': worker_id}
        resp_session_id = requests.get('http://127.0.0.1:5052/insert_session',params=insert_session_payload)
        session_id = resp_session_id.json()["data"]
        session_id_store[worker_id] = session_id
        db_response_attn = requests.get('http://127.0.0.1:5052/get_existing_attn_tweets_new?worker_id='+str(worker_id)+"&page=NA&feedtype="+feedtype)
        db_response_attn = db_response_attn.json()['data']
        db_response_timeline = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page=NA&feedtype="+feedtype)
        db_response_timeline = db_response_timeline.json()['data']
        attn_payload = []
        attn_pages = []
        print(db_response_attn)
        for attn_tweet in db_response_attn:
            db_tweet = {
                'tweet_id': attn_tweet[0],
                'page' : attn_tweet[2],
                'rank' : attn_tweet[3],
                'present' : attn_tweet[1]
            }
            attn_payload.append(db_tweet)
            attn_pages.append(int(attn_tweet[2]))
        max_page_store[worker_id] = max(attn_pages)
        timeline_payload = []
        for timeline_tweet in db_response_timeline:
            db_tweet = {
                'fav_before': timeline_tweet[2],
                'tid' : timeline_tweet[0],
                'rtbefore' : timeline_tweet[3],
                'page' : timeline_tweet[4],
                'rank' : timeline_tweet[5],
                'predicted_score' : timeline_tweet[6]
            }
            timeline_payload.append(db_tweet)
        finalJson = []
        finalJson.append(session_id)
        finalJson.append(feedtype)
        finalJson.append(timeline_payload)
        finalJson.append(attn_payload)
        requests.post('http://127.0.0.1:5052/insert_timelines_attention_in_session',json=finalJson)
    else:
        session_id = session_id_store[worker_id]
    if attn == 1:
        db_response = requests.get('http://127.0.0.1:5052/get_existing_attn_tweets_new?worker_id='+str(worker_id)+"&page="+str(page)+"&feedtype="+feedtype)
        db_response = db_response.json()['data']
        public_tweets = [d[2] for d in db_response]     
    else:
        print("page:::")
        print(page)
        print(worker_id)   
        db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page="+str(page)+"&feedtype="+feedtype)
        db_response = db_response.json()['data']
        if db_response == "NEW":
            feed_json = []
            feed_json.append({"anything_present":"NO"})
            return jsonify(feed_json)
        public_tweets = [d[4] for d in db_response]
        public_tweets_v2 = [d[5] for d in db_response]

    feed_json = []
    rankk = 1

    for (tweet_en,tweet) in enumerate(public_tweets): # Modify what tweet is for this loop in order to change the logic ot use our data or twitters.

        # Checking for an image in the tweet. Adds all the links of any media type to the eimage list.
        tweet_v2 = public_tweets_v2[tweet_en]
        actor_name = tweet["user"]["name"]
        full_text = tweet["full_text"]
        url_start = []
        url_end = []
        url_display = []
        url_extend = []
        url_actual = []
        if "entities" in tweet.keys():
            if "urls" in tweet["entities"]:
                for url_dict in tweet["entities"]["urls"]:
                    url_start.append(url_dict["indices"][0])
                    url_end.append(url_dict["indices"][1])
                    url_display.append(url_dict["display_url"])
                    url_extend.append(url_dict["expanded_url"])
                    url_actual.append(url_dict["url"])

        last_url_arr = re.findall("(?P<url>https?://[^\s]+)", full_text)
        if last_url_arr:
            last_url = last_url_arr[-1]
            if last_url not in url_actual:
                full_text = full_text.replace(last_url,'')

        full_text_json = []
        
        if url_actual:
            normal_idx = 0
            url_idx = 0
            for i in range(len(url_start)):
                url_idx_start = url_start[i]
                full_text_json.append({"text":full_text[normal_idx:url_idx_start],"url":""})
                full_text_json.append({"text":url_extend[i],"url":url_extend[i]})
                normal_idx = url_end[i]
            if normal_idx < len(full_text):
                full_text_json.append({"text":full_text[normal_idx:len(full_text)],"url":""})
        else:
            full_text_json.append({"text":full_text,"url":""})
        
        isRetweet = False 
        retweeted_by = ""
        actor_picture = tweet["user"]["profile_image_url"]
        actor_username = tweet["user"]["screen_name"]
        tempLikes = tweet["favorite_count"]
        quoted_by = ""
        quoted_by_text = ""
        quoted_by_actor_username = ""
        quoted_by_actor_picture = ""
        isQuote = False
        try: # This will handle retweet case and nested try will handle retweeted quote
            full_text = tweet["retweeted_status"]["full_text"]
            retweeted_by = actor_name # Grab it here before changing the name
            # Now I need to check if the retweeted status is a quoted status I think. 
            try:
                full_text = tweet["retweeted_status"]["quoted_status"]["full_text"]
                quoted_by = tweet["retweeted_status"]["user"]["name"]         # name of the retweet who quoted
                quoted_by_text = tweet["retweeted_status"]["full_text"]
                quoted_by_actor_username = tweet["retweeted_status"]["user"]["screen_name"]
                quoted_by_actor_picture = tweet["retweeted_status"]["user"]["profile_image_url"]
                actor_name = tweet["retweeted_status"]["quoted_status"]["user"]["name"] # original tweeter info used below.
                actor_username = tweet["retweeted_status"]["quoted_status"]["user"]["screen_name"]
                actor_picture = tweet["retweeted_status"]["quoted_status"]["user"]["profile_image_url"]
                tempLikes = tweet["retweeted_status"]["quoted_status"]["favorite_count"]
                isQuote = True
                
            except: # if its not a quote default to normal retweet settings
                actor_name = tweet["retweeted_status"]["user"]["name"] # original tweeter info used below.
                actor_username = tweet["retweeted_status"]["user"]["screen_name"]
                actor_picture = tweet["retweeted_status"]["user"]["profile_image_url"]
                tempLikes = tweet["retweeted_status"]["favorite_count"]
                isRetweet = True
            isRetweet = True
        except:
            isRetweet = False

        if not isRetweet: # case where its not a retweet but still could be a quote.
            try:
                full_text = tweet["quoted_status"]["full_text"]
                quoted_by = tweet["user"]["name"]         # name of the person who quoted
                quoted_by_text = tweet["full_text"]
                quoted_by_actor_username = tweet["user"]["screen_name"]
                quoted_by_actor_picture = tweet["user"]["profile_image_url"]
                actor_name = tweet["quoted_status"]["user"]["name"] # original tweeter info used below.
                actor_username = tweet["quoted_status"]["user"]["screen_name"]
                actor_picture = tweet["quoted_status"]["user"]["profile_image_url"]
                #tempLikes = tweet["quoted_status"]["favorite_count"]
                isQuote = True
            except:
                isQuote = False

        entities_keys = ""
        all_urls = ""
        urls_list = []
        expanded_urls_list = []
        urls = ""
        expanded_urls = ""
        image_raw = ""
        picture_heading = ""
        picture_description = ""
        mediaArr = ""
        # Decision making for the block to retrieve article cards AND embedded images

        if isQuote and isRetweet: # Check for the case of a quote within a retweet.
            if "entities" in tweet["retweeted_status"]["quoted_status"].keys(): 
                entities_keys = tweet["retweeted_status"]["quoted_status"]["entities"].keys()
                mediaArr = tweet["retweeted_status"]["quoted_status"]['entities'].get('media',[])
            if "urls" in entities_keys:
                all_urls = tweet["retweeted_status"]["quoted_status"]["entities"]["urls"]
        elif isQuote: #  quote only case
            if "entities" in tweet["quoted_status"].keys():
                entities_keys = tweet["quoted_status"]["entities"].keys()
                mediaArr = tweet["quoted_status"]['entities'].get('media',[])
            if "urls" in entities_keys:
                all_urls = tweet["quoted_status"]["entities"]["urls"]
        elif isRetweet:
            if "entities" in tweet["retweeted_status"].keys():
                entities_keys = tweet["retweeted_status"]["entities"].keys()
                mediaArr = tweet["retweeted_status"]['entities'].get('media',[])
            if "urls" in entities_keys:
                all_urls = tweet["retweeted_status"]["entities"]["urls"]
        else:
            if "entities" in tweet.keys():
                entities_keys = tweet["entities"].keys()
                mediaArr = tweet['entities'].get('media',[])
            if "urls" in entities_keys:
                all_urls = tweet["entities"]["urls"]


        # Embedded image retrieval (edited to handle retweets also now)
        hasEmbed = False
        eimage = []
        try: # Not sure why this has an issue all of a sudden.
            flag_image = False   
            if len(mediaArr) > 0:    
                for x in range(len(mediaArr)):
                    eimage.append(mediaArr[x]['media_url'])
                    flag_image = True
                    '''
                    if mediaArr[x]['type'] == 'photo':
                        hasEmbed = True
                        if "sizes" in mediaArr[x].keys():
                            if "small" in mediaArr[x]["sizes"].keys():
                                small_width = int(mediaArr[x]["sizes"]["small"]["w"])
                                small_height = int(mediaArr[x]["sizes"]["small"]["h"])
                                small_aspect_ratio = small_height/small_width
                                if small_aspect_ratio > 0.89:
                                    if "thumb" in mediaArr[x]["sizes"].keys():
                                        eimage.append(mediaArr[x]['media_url']+':thumb')
                                    else:
                                        eimage.append(mediaArr[x]['media_url']+':small')
                                else:
                                    eimage.append(mediaArr[x]['media_url']+':small')
                            else:
                                eimage.append(mediaArr[x]['media_url'])
                        else:
                            eimage.append(mediaArr[x]['media_url'])
                        flag_image = True  
                    ''' 
            if not flag_image:
                eimage.append("") 
        except Exception as error:
            print(error)
            eimage[0] = ""


            # Redesigned block to retrieve the CardInfo data.
        if "urls" in entities_keys and not hasEmbed:
            for each_url in all_urls:
                urls_list.append(each_url["url"])
                expanded_urls_list.append(each_url["expanded_url"])
            urls = ",".join(urls_list)
            expanded_urls = ",".join(expanded_urls_list)
        if len(expanded_urls_list) > 0 and not isQuote and not hasEmbed: # not isQuote is to save time in the case of a quote. no card needed
            card_url = expanded_urls_list[0]
            card_data = CardInfo.getCardData(card_url)
            if card_data:
                if "image" in card_data.keys():
                    image_raw = card_data['image']
                    picture_heading = card_data["title"]
                    picture_description = card_data["description"]
        #if isRetweet:
            #print("Is a retweet.")

        for urll in urls_list:
            full_text = full_text.replace(urll,"")
        #print(full_text)
        full_text = xml.sax.saxutils.unescape(full_text)

        body = html.unescape(full_text)
        date_string_temp = tweet['created_at']
        created_date_datetime = parser.parse(date_string_temp)
        td = (datetime.datetime.now(datetime.timezone.utc) - created_date_datetime)
        hours, remainder = divmod(td.seconds, 3600) # can we scrap this and the line below ______-------________-----________---------______--------
        minutes, seconds = divmod(remainder, 60)
        time = ""
        if minutes < 10:
            time = "-00:0"+str(minutes)
        else:
            time = "-00:"+str(minutes)
        #time.append(td.seconds)
        # Fixing the like system
        finalLikes = ""
        if (tempLikes <= 999):
            finalLikes = str(tempLikes)
        elif (tempLikes >= 1000):
            counterVar = 1
            while(True):
                if (tempLikes - 1000 > 0):
                    tempLikes = tempLikes - 1000
                    counterVar = counterVar + 1
                else:
                    finalLikes = str(counterVar) + "." + str(tempLikes)[0] + "k"
                    break

        # Fixing the retweet system
        finalRetweets = ""
        tempRetweets = tweet["retweet_count"]
        if (tempRetweets <= 999):
            finalRetweets = str(tempRetweets)
        elif (tempRetweets >= 1000):
            counterVar = 1
            while(True):
                if (tempRetweets - 1000 > 0):
                    tempRetweets = tempRetweets - 1000
                    counterVar = counterVar + 1
                else:
                    finalRetweets = str(counterVar) + "." + str(tempRetweets)[0] + "k"
                    break

        profile_link = ""
        if tweet["user"]["url"]:
            profile_link = tweet["user"]["url"]
        
        feed = {
            'body':body,
            'body_json':full_text_json,
            'likes': finalLikes,
            'urls':urls,
            'expanded_urls':expanded_urls,
            'experiment_group':'var1',
            'post_id':rankk,
            'tweet_id':str(tweet["id"]),
            'worker_id':str(worker_id),
            'rank':str(rankk),
            'picture':image_raw.replace("http:", "https:"),
            'picture_heading':picture_heading,
            'picture_description':picture_description,
            'actor_name':actor_name,
            'actor_picture': actor_picture.replace("http:", "https:"),
            'actor_username': actor_username,
            'time':time,
            'embedded_image': eimage[0].replace("http:", "https:"),
            'retweet_count': finalRetweets,
            'profile_link': profile_link,
            'user_retweet': str(tweet['retweeted']),
            'user_fav': str(tweet['favorited']),
            'retweet_by': retweeted_by,
            'quoted_by': quoted_by,
            'quoted_by_text' : quoted_by_text,
            'quoted_by_actor_username' : quoted_by_actor_username,
            'quoted_by_actor_picture' : quoted_by_actor_picture.replace("http:", "https:")
        }
        feed_json.append(feed)
        rankk = rankk + 1
    #last_feed_value = {'new_random_identifier' : new_random_identifier}
    #feed_json.append(last_feed_value)
    last_feed_value = {'session_id' : session_id, 'max_pages' : max_page_store[worker_id], 'anything_present' : 'YES'}
    feed_json.append(last_feed_value)
    return jsonify(feed_json)

@app.route('/completedstatuschange', methods=['GET','POST'])
def completed_status_change():
    worker_id = str(request.args.get('worker_id')).strip()
    completed_survey[worker_id] = True
    return "Done!"

@app.route('/completedcheck', methods=['GET','POST'])
def completed_check():
    worker_id = str(request.args.get('worker_id')).strip()
    print(completed_survey[worker_id])
    if not completed_survey[worker_id]:
        return "NO"
    return "YES"

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_message='uncaught exception'), 500

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response
  
if __name__ == '__main__':
    app.run(host="0.0.0.0")
