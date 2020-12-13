""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
import tweepy
import json
from flask import Flask, render_template, request, url_for, jsonify

app = Flask(__name__)

app.debug = False

@app.route('/retweet/', methods=['POST'])
def retweet():
    cred = {}
    f = open("guest_credentials.txt")
    for line in f:
        name, value = line.split(":")
        cred[name] = value.strip()
    f.close()

    auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
    auth.set_access_token(cred["token"], cred["token_secret"])
    api = tweepy.API(auth)

    data = request.get_json()
    tweet_id = data['tweet_id']
    try:
        api.retweet(int(tweet_id))
        return jsonify({"success":1}) # Retweet successful
    except Exception as e:
        print(e)
        return jsonify({"success":0}) # Retweet failed

@app.route('/like/', methods=['POST'])
def like():
    cred = {}
    f = open("guest_credentials.txt")
    for line in f:
        name, value = line.split(":")
        cred[name] = value.strip()
    f.close()

    auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
    auth.set_access_token(cred["token"], cred["token_secret"])
    api = tweepy.API(auth)

    data = request.get_json()
    tweet_id = data['tweet_id']
    try:
        tweet = api.get_status(int(tweet_id))
        tweet.favorite()
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