import os
import numpy as np
from flask import Flask, render_template, request, url_for, redirect, flash, make_response
import requests
import random, string
import datetime
from requests_oauthlib import OAuth1Session
#from src.databaseAccess.database_config import config
from configparser import ConfigParser
from collections import defaultdict
import logging
import json

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

def break_timeline_attention(public_tweets):
    db_tweet_payload = []
    db_tweet_attn_payload = []
    rankk = 0
    tweetids_by_page = defaultdict(list)
    all_tweet_ids = [tweet['id'] for tweet in public_tweets]
    for tweet in public_tweets:
        page = int(rankk/10)
        rank_in_page = (rankk%10) + 1
        db_tweet = {
            'fav_before':str(tweet['favorited']),
            'tid':str(tweet["id"]),
            'rtbefore':str(tweet['retweeted']),
            'page':page,
            'rank':rank_in_page
        }
        db_tweet_payload.append(db_tweet)
        tweetids_by_page[page].append(tweet["id"])
        rankk = rankk + 1
    for attn_page in range(4):
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
    return db_tweet_payload,db_tweet_attn_payload

webInformation = config('../configuration/config.ini','webconfiguration')

app_callback_url = str(webInformation['callback'])
app_callback_url_qual = str(webInformation['qualcallback'])
request_token_url = str(webInformation['request_token_url'])
access_token_url = str(webInformation['access_token_url'])
authorize_url = str(webInformation['authorize_url'])
show_user_url = str(webInformation['show_user_url'])
rockwell_url = str(webInformation['app_route'])
account_settings_url = str(webInformation['account_settings_url'])

oauth_store = {}
start_url_store = {}
screenname_store = {}
userid_store = {}
worker_id_store = {}
access_token_store = {}
access_token_secret_store = {}

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
    start_url = start_url_store[oauth_token_qualtrics]
    res = make_response(render_template('YouGovQualtrics.html', start="Yes", start_url=start_url, oauth_token=oauth_token_qualtrics, insertfeedurl="http://127.0.0.1:5000/insertfeedqualtrics"))
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
        return redirect('http://' + str(webInformation['url']) + ':5000')

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

    insert_user_payload = {'twitter_id': str(user_id),'access_token': real_oauth_token, 'access_token_secret': real_oauth_token_secret, 'screenname': screen_name, 'account_settings': account_settings_user}
    resp_worker_id = requests.get('http://' + webInformation['localhost'] + ':5052/insert_user',params=insert_user_payload)
    worker_id = resp_worker_id.json()["data"]
    
    #screenname_store[oauth_token] = screen_name
    #userid_store[oauth_token] = user_id
    #worker_id_store[oauth_token] = str(worker_id)
    #access_token_store[oauth_token] = real_oauth_token
    #access_token_secret_store[oauth_token] = real_oauth_token_secret
    del oauth_store[oauth_token]

    res = make_response(render_template('YouGovQualtrics.html', start="No", worker_id=worker_id, oauth_token=oauth_token, insertfeedurl="http://127.0.0.1:5000/insertfeedqualtrics"))
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
    print("Called!!!")
    worker_id = request.args.get('worker_id').strip()
    oauth_token = request.args.get('oauth_token')
    db_response = requests.get('http://127.0.0.1:5052/get_existing_user?worker_id='+str(worker_id))
    print(db_response.json())
    db_response = db_response.json()['data']
    access_token = db_response[0][0]
    access_token_secret = db_response[0][1]
    screenname = db_response[0][2]
    userid = db_response[0][3]
    db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page="+str(0)+"&feedtype=S")
    need_to_fetch_tweets = False
    if db_response.json()['data'] == "NEW":
        need_to_fetch_tweets = True
    else:
        last_updated_date_str = db_response.json()['data'][0][1]
        last_updated_date = datetime.datetime.strptime(last_updated_date_str,'%Y-%m-%d %H:%M:%S')
        datetime_now = datetime.datetime.now()
        diff = datetime_now - last_updated_date
        days, seconds = diff.days, diff.seconds
        hours = days * 24 + seconds // 3600
        if hours > 24:
            need_to_fetch_tweets = True
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
        params = {"count": "80","tweet_mode": "extended"}
        response = oauth.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params = params)
        if response.text == '{"errors":[{"code":89,"message":"Invalid or expired token."}]}':
            return "Invalid Token"
        if response.text == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
            print("Rate limit exceeded.")
        public_tweets = json.loads(response.text)
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
        timeline_json = [public_tweets,public_tweets_user,screenname]
        recsys_response = requests.get('http://127.0.0.1:5053/recsys_rerank',json=timeline_json)
        public_tweets_control = recsys_response.json()['data']
        db_tweet_payload = []
        for tweet in public_tweets:
            db_tweet = {
                'tweet_id':tweet["id"],
                'tweet_json':tweet
            }
            db_tweet_payload.append(db_tweet)
        db_tweet_chronological_payload,db_tweet_chronological_attn_payload = break_timeline_attention(public_tweets)
        db_tweet_control_payload,db_tweet_control_attn_payload = break_timeline_attention(public_tweets_control)
        finalJson = []
        finalJson.append(db_tweet_payload)
        finalJson.append(db_tweet_chronological_payload)
        finalJson.append(db_tweet_chronological_attn_payload)
        finalJson.append(db_tweet_control_payload)
        finalJson.append(db_tweet_control_attn_payload)
        finalJson.append(worker_id)
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
    return "Done!"

@app.route('/auth/getscreenname')
def screenname():
    #print("GET SCEEN NAME CALLED!!!")
    oauth_token_qualtrics = request.args.get('oauth_token')
    screen_name_return = screenname_store[oauth_token_qualtrics]
    if screen_name_return == "####":
        return screen_name_return
    random_identifier_len = random.randint(15, 26)    
    random_identifier = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random_identifier_len))
    userid_return = userid_store[oauth_token_qualtrics]
    worker_id_return = worker_id_store[oauth_token_qualtrics]
    access_token_return = access_token_store[oauth_token_qualtrics]
    access_token_secret_return = access_token_secret_store[oauth_token_qualtrics]
    return screen_name_return+"$$$"+str(userid_return)+"$$$"+worker_id_return+"$$$"+access_token_return+"$$$"+access_token_secret_return+"$$$"+random_identifier

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
