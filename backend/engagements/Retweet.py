""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
#import tweepy
from requests_oauthlib import OAuth1Session
from configparser import ConfigParser
import requests
import json
from flask import Flask, render_template, request, url_for, jsonify

app = Flask(__name__)

app.debug = False

def config(filename,section):
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

@app.route('/retweet', methods=['POST'])
def retweet():
    data = request.get_json()
    data_arg = data['arguments']
    tweet_id = data_arg.split(',')[0].strip()
    session_id = data_arg.split(',')[1].strip()
    access_token = data_arg.split(',')[2].strip()
    access_token_secret = data_arg.split(',')[3].strip()
    cred = config('../../config.ini','twitterapp')

    #auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
    #auth.set_access_token(cred["token"], cred["token_secret"])
    #api = tweepy.API(auth)
    oauth = OAuth1Session(cred['key'],
                       client_secret=cred['key_secret'],
                       resource_owner_key=access_token,
                       resource_owner_secret=access_token_secret)

    try:
        #api.retweet(int(tweet_id))
        #params = {"id": int(tweet_id)}
        response_retweet = oauth.post("https://api.twitter.com/1.1/statuses/retweet/"+tweet_id+".json")
        #requests.post('http://127.0.0.1:5052/update_tweet_retweet?tweet_id='+str(tweet_id)+'&session_id='+str(session_id))
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.route('/like', methods=['POST'])
def like():
    data = request.get_json()
    data_arg = data['arguments']
    tweet_id = data_arg.split(',')[0].strip()
    session_id = data_arg.split(',')[1].strip()
    access_token = data_arg.split(',')[2].strip()
    access_token_secret = data_arg.split(',')[3].strip()
    cred = config('../../config.ini','twitterapp')

    #auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
    #auth.set_access_token(cred["token"], cred["token_secret"])
    #api = tweepy.API(auth)
    oauth = OAuth1Session(cred['key'],
                       client_secret=cred['key_secret'],
                       resource_owner_key=access_token,
                       resource_owner_secret=access_token_secret)
    try:
        #tweet = api.get_status(int(tweet_id))
        #tweet.favorite()
        response_like = oauth.post("https://api.twitter.com/1.1/favorites/create.json",params = {"id":int(tweet_id)})
        #requests.post('http://127.0.0.1:5052/update_tweet_like?tweet_id='+str(tweet_id)+'&session_id='+str(session_id))
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.route('/link', methods=['POST'])
def link():
    data = request.get_json()
    data_arg = data['arguments']
    tweet_id = data_arg.split(',')[0].strip()
    session_id = data_arg.split(',')[1].strip()
    urll = data_arg.split(',')[2].strip()
    iscard = data_arg.split(',')[3].strip()

    try:
        #tweet = api.get_status(int(tweet_id))
        #tweet.favorite()
        requests.post('http://127.0.0.1:5052/insert_click?tweet_id='+str(tweet_id)+'&session_id='+str(session_id)+'&urll='+str(urll)+'&iscard='+str(iscard))
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.route('/tracking', methods=['POST'])
def tracking():
    data = request.get_json()
    session_id = data['session_id']
    furthestSeen = data['furthestSeen']
    try:
        #tweet = api.get_status(int(tweet_id))
        #tweet.favorite()
        requests.post('http://127.0.0.1:5052/insert_tracking?session_id='+str(session_id)+'&furthestSeen='+str(furthestSeen))
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.route('/check_attn', methods=['GET','POST'])
def check_attn():
    data = request.get_json()
    worker_id = data['worker_id']
    page = int(data['page'])
    attn_map = data['attn_map']
    print(attn_map)
    try:
        db_response = requests.get('http://127.0.0.1:5052/get_prereg_tweets?worker_id='+str(worker_id)+'&attnlevel='+str(page+1))
        db_response = db_response.json()['data']
        actual_ans = [d[1] for d in db_response]
        print(actual_ans)
        check = "Correct"
        for i in range(4):
            if bool(attn_map[i]) != actual_ans[i]:
                check = "Incorrect"
                break
        return jsonify({"check":check})
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    app.run(host = "127.0.0.1", port = 5050)
    # app.run(ssl_context='adhoc', host = "0.0.0.0", port = 5050) To add SSL
