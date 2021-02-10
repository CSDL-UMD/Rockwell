import os
from flask import Flask, render_template, request, url_for, redirect
import pandas as pd
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
truman_url = 'http://127.0.0.1/'

workerId = ""
assignmentId = ""
hitId = ""

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
caller = {}


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start():
    data = request.get_json()
    calling_from = data['calling']
    caller['calling_from'] = calling_from
    if calling_from == 'screening':
        workerId = request.args.get('workerId')
        assignmentId = request.args.get('assignmentId')
        hitId = request.args.get('hitId')
        f = open("/home/saumya/Documents/USF/Project/ASD/mock_social_media_platform/infodiversity-mock-social-media/twitter_api/twauth-web-master/mturk_indentifiers.txt",'w')
        f.write(workerId+"\n")
        f.write(assignmentId+"\n")
        f.write(hitId)
        f.close()
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
        return render_template('start.html', authorize_url=authorize_url, oauth_token=oauth_token, request_token_url=request_token_url)

    elif calling_from == 'truman':
        # note that the external callback URL must be added to the whitelist on
        # the developer.twitter.com portal, inside the app settings
        # app_callback_url = url_for('callback', _external=True)
        app_callback_url = "http://127.0.0.1:5000/callback"
        print("CALLBACK : "+app_callback_url)
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

        print("CONTENT : "+content.text)
        
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
        return redirect(authorize_url + '?oauth_token=' + oauth_token)


@app.route('/callback')
def callback():
    calling_from = caller['calling_from']
    if calling_from == "screening":
        f = open("/home/saumya/Documents/USF/Project/ASD/mock_social_media_platform/infodiversity-mock-social-media/twitter_api/twauth-web-master/mturk_indentifiers.txt",'r')
        mturk_identifiers = f.read()
        f.close()
        workerId = mturk_identifiers.split("\n")[0]
        assignmentId = mturk_identifiers.split("\n")[1]
        hitId = mturk_identifiers.split("\n")[2]
        # Accept the callback params, get the token and call the API to
        # display the logged-in user's name and handle
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
        screen_name = access_token[3].split("=")[1]

        #screen_name = access_token[b'screen_name'].decode('utf-8')
        #user_id = access_token[b'user_id'].decode('utf-8')

        # These are the tokens you would store long term, someplace safe
        #real_oauth_token = access_token[b'oauth_token'].decode('utf-8')
        #real_oauth_token_secret = access_token[b'oauth_token_secret'].decode(
        #    'utf-8')

        f = open('guest_credentials.txt','w')
        f.write('key:'+str(app.config['APP_CONSUMER_KEY'])+'\n')
        f.write('key_secret:'+str(app.config['APP_CONSUMER_SECRET'])+'\n')
        f.write('token:'+str(real_oauth_token)+'\n')
        f.write('token_secret:'+str(real_oauth_token_secret))
        f.close()

        # Call api.twitter.com/1.1/users/show.json?user_id={user_id}
        #real_token = oauth.Token(real_oauth_token, real_oauth_token_secret)
        #real_client = oauth.Client(consumer, real_token)
        #real_resp, real_content = real_client.request(
        #    show_user_url + '?user_id=' + user_id, "GET")

        oauth_show_user = OAuth1Session(client_key=app.config['APP_CONSUMER_KEY'],client_secret=app.config['APP_CONSUMER_SECRET'],
        	resource_owner_key=real_oauth_token,resource_owner_secret=real_oauth_token_secret)
        real_content = oauth_show_user.get(show_user_url + '?user_id=' + user_id)
        #if real_resp['status'] != '200':
        #    error_message = "Invalid response from Twitter API GET users/show: {status}".format(
        #        status=real_resp['status'])
        #    return render_template('error.html', error_message=error_message)

        #response = json.loads(real_content.decode('utf-8'))

        #response = json.loads(real_content.json())     

        response = real_content.json()

        friends_count = response['friends_count']
        statuses_count = response['statuses_count']
        followers_count = response['followers_count']
        name = response['name']

        f = open("/home/saumya/Documents/USF/Project/ASD/mock_social_media_platform/infodiversity-mock-social-media/twitter_api/twauth-web-master/screening_result.csv",'w')
        f.write("Worker ID,Assignment ID,Hit ID,Twitter ID,Twitter handle,Friends Count,Statuses Count,Followers Count\n")
        values = ','.join([workerId,assignmentId,hitId,user_id,screen_name,str(friends_count),str(statuses_count),str(followers_count)])
        f.write(values)
        f.close()

        # don't keep this token and secret in memory any longer
        del oauth_store[oauth_token]

        return render_template('callback-success.html', screen_name=screen_name, user_id=user_id, name=name,
                               friends_count=friends_count, statuses_count=statuses_count, followers_count=followers_count, access_token_url=access_token_url)
    
    elif calling_from == "truman":
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
        del caller['calling_from']

        return redirect(truman_url + '?access_token=' + real_oauth_token + '&access_token_secret=' + real_oauth_token_secret)


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_message='uncaught exception'), 500

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Origin,Content-Type,Authorization,X-Auth-Token')
    return response
  
if __name__ == '__main__':
    app.run()
