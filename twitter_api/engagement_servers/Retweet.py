""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
#import tweepy
from requests_oauthlib import OAuth1Session
import json
from flask import Flask, render_template, request, url_for, jsonify

app = Flask(__name__)

app.debug = False

@app.route('/retweet/', methods=['POST'])
def retweet():
    data = request.get_json()
    tweet_id = data['tweet_id']
    access_token = data['access_token']
    access_token_secret = data['access_token_secret']
    cred = {}
    f = open("guest_credentials_2.txt")
    for line in f:
        name, value = line.split(":")
        cred[name] = value.strip()
    f.close()

    #auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
    #auth.set_access_token(cred["token"], cred["token_secret"])
    #api = tweepy.API(auth)
    oauth = OAuth1Session(cred['key'],
                       client_secret=cred['key_secret'],
                       access_token,
                       access_token_secret)

    try:
        #api.retweet(int(tweet_id))
        #params = {"id": int(tweet_id)}
        response_retweet = oauth.post("https://api.twitter.com/1.1/statuses/retweet/"+tweet_id+".json")
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.route('/like/', methods=['POST'])
def like():
    data = request.get_json()
    tweet_id = data['tweet_id']
    access_token = data['access_token']
    access_token_secret = data['access_token_secret']
    cred = {}
    f = open("guest_credentials.txt")
    for line in f:
        name, value = line.split(":")
        cred[name] = value.strip()
    f.close()

    #auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
    #auth.set_access_token(cred["token"], cred["token_secret"])
    #api = tweepy.API(auth)
    oauth = OAuth1Session(cred['key'],
                       client_secret=cred['key_secret'],
                       resource_owner_key=cred['token'],
                       resource_owner_secret=cred['token_secret'])

    data = request.get_json()
    tweet_id = data['tweet_id']
    try:
        #tweet = api.get_status(int(tweet_id))
        #tweet.favorite()
        response_like = oauth.post("https://api.twitter.com/1.1/favorites/create.json",params = {"id":int(tweet_id)})
        print(response_like)
        return jsonify({"success":1}) # Retweet successful
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