import os
from flask import Flask, render_template, request, url_for, redirect
#import oauth2 as oauth
#import urllib.request
from requests_oauthlib import OAuth1Session
#import requests
#import urllib.parse
#import urllib.error
import json

app = Flask(__name__)

app.debug = False

request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
authorize_url = 'https://api.twitter.com/oauth/authorize'
show_user_url = 'https://api.twitter.com/1.1/users/show.json'
truman_url = 'http://127.0.0.1:3000'

# Support keys from environment vars (Heroku).
#app.config['APP_CONSUMER_KEY'] = os.getenv(
#    'TWAUTH_APP_CONSUMER_KEY', 'API_Key_from_Twitter')
#app.config['APP_CONSUMER_SECRET'] = os.getenv(
#    'TWAUTH_APP_CONSUMER_SECRET', 'API_Secret_from_Twitter')

# alternatively, add your key and secret to config.cfg
# config.cfg should look like:
# APP_CONSUMER_KEY = 'API_Key_from_Twitter'
# APP_CONSUMER_SECRET = 'API_Secret_from_Twitter'
app.config.from_pyfile('config.cfg', silent=True)

oauth_store = {}


#@app.route('/')
#def hello():
 #   return render_template('index.html')


@app.route('/')
def start():
    # note that the external callback URL must be added to the whitelist on
    # the developer.twitter.com portal, inside the app settings
    app_callback_url = url_for('callback', _external=True)
    # Generate the OAuth request tokens, then display them
    """
    consumer = oauth.Consumer(
        app.config['APP_CONSUMER_KEY'], app.config['APP_CONSUMER_SECRET'])
    client = oauth.Client(consumer)
    resp, content = client.requests(request_token_url, "POST", body=urllib.parse.urlencode({
                                   "oauth_callback": app_callback_url}))
    """
    request_token = OAuth1Session(client_key=app.config['APP_CONSUMER_KEY'],client_secret=app.config['APP_CONSUMER_SECRET'])
    content = request_token.post(request_token_url, data = {"oauth_callback":app_callback_url})
    
    #if resp['status'] != '200':
    #    error_message = 'Invalid response, status {status}, {message}'.format(
    #        status=resp['status'], message=content.decode('utf-8'))
     #   return render_template('error.html', error_message=error_message)

    #request_token = dict(urllib.parse.parse_qsl(content))
    #oauth_token = request_token[b'oauth_token'].decode('utf-8')
    #oauth_token_secret = request_token[b'oauth_token_secret'].decode('utf-8')

    data_tokens = content.text.split("&")

    oauth_token = data_tokens[0].split("=")[1]
    oauth_token_secret = data_tokens[1].split("=")[1] 

    oauth_store[oauth_token] = oauth_token_secret
    return render_template('index.html', authorize_url=authorize_url, oauth_token=oauth_token, request_token_url=request_token_url)


@app.route('/callback')
def callback():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    oauth_denied = request.args.get('denied')

    # if the OAuth request was denied, delete our local token
    # and show an error message
    if oauth_denied:
        if oauth_denied in oauth_store:
            del oauth_store[oauth_denied]
        return render_template('error.html', error_message="the OAuth request was denied by this user")

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
    
    oauth_access_tokens = OAuth1Session(client_key=app.config['APP_CONSUMER_KEY'],client_secret=app.config['APP_CONSUMER_SECRET'],
        resource_owner_key=oauth_token,resource_owner_secret=oauth_token_secret,verifier=oauth_verifier)
    content = oauth_access_tokens.post(access_token_url)  

    #access_token = dict(urllib.parse.parse_qsl(content))

    access_token = content.text.split("&")

    # These are the tokens you would store long term, someplace safe
    real_oauth_token = access_token[0].split("=")[1]
    real_oauth_token_secret = access_token[1].split("=")[1]
    user_id = access_token[2].split("=")[1]

    del oauth_store[oauth_token]

    return redirect(truman_url + '?access_token=' + real_oauth_token + '&access_token_secret=' + real_oauth_token_secret)

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_message='uncaught exception'), 500

  
if __name__ == '__main__':
    app.run()
