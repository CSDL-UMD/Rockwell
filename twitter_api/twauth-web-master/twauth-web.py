import os
from flask import Flask, render_template, request, url_for, redirect
#import oauth2 as oauth
#import urllib.request
import requests
import datetime
from requests_oauthlib import OAuth1Session
from configparser import ConfigParser
#import logging
#import requests
#import urllib.parse
#import urllib.error
import json

app = Flask(__name__)

app.debug = False
#log_level = logging.DEBUG
#logging.basicConfig(filename='authorizer.log', level=log_level)

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

oauth_store = {}

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
        #logging.error('Error in reading config file : Section {0} not found in the {1} file'.format(section, filename))
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db

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
    cred = config('../../config.ini','twitterapp')
    request_token = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'])
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
    # Trying to add a browser cookie
    s = request.Session() # Current session
    ckies = s.get('https://http://infodiversity.cse.usf.edu/cookies') # grab all client cookies at our link
    print("Cookies: " + str(ckies.cookies)) # Print to confirm we have cookies
    test = False
    for ck in ckies.cookies:
        if(ck.name == "Exp"):
            test = True
    if(test): # change to if "cookie name" cause if it exists we dont want to make another.
        print("No need to make a cookie we have one.")
    else:
        print("Making a cookie")
        cookie = {
            "name": 'Exp',
            "creation": datetime.now() # use datetime.timedelta (may have to cast this to a datetime object in guest access) https://docs.python.org/3/library/datetime.html
        }
        s.get('https://http://infodiversity.cse.usf.edu/cookies', cookies=cookie) # post the cookie
    # End of cookie code
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
    
    cred = config('../../config.ini','twitterapp')
    oauth_access_tokens = OAuth1Session(client_key=cred['key'],client_secret=cred['key_secret'],resource_owner_key=oauth_token,resource_owner_secret=oauth_token_secret,verifier=oauth_verifier)
    content = oauth_access_tokens.post(access_token_url)  

    #access_token = dict(urllib.parse.parse_qsl(content))

    access_token = content.text.split("&")

    # These are the tokens you would store long term, someplace safe
    real_oauth_token = access_token[0].split("=")[1]
    real_oauth_token_secret = access_token[1].split("=")[1]
    user_id = access_token[2].split("=")[1]
    screen_name = access_token[3].split("=")[1]

    resp_worker_id = requests.get('http://127.0.0.1:5052/insert_user?twitter_id='+str(user_id)+'&screen_name='+str(screen_name))
    worker_id = resp_worker_id.json()["data"]

    print(worker_id)

    del oauth_store[oauth_token]

    #redirect(truman_url + '?access_token=' + real_oauth_token + '&access_token_secret=' + real_oauth_token_secret)
    print(real_oauth_token,real_oauth_token_secret)

    return render_template('placeholder.html', worker_id=worker_id, access_token=real_oauth_token, access_token_secret=real_oauth_token_secret)

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_message='uncaught exception'), 500

  
if __name__ == '__main__':
    app.run()
