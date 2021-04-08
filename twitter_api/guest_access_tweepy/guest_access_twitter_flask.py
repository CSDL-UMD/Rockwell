""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
import os
#import random
#import string
#import glob
#import tweepy
#import pandas as pd # No longer needed?
#import ../database_access/access_object.py
import datetime
import json
import Cardinfo
import requests
#import TweetObject
from flask import Flask, render_template, request, url_for, jsonify
from requests_oauthlib import OAuth1Session
import xml
import xml.sax.saxutils
#import requests as rq

app = Flask(__name__)

app.debug = False

@app.route('/getfeed', methods=['GET'])
def get_feed():

	access_token = request.args.get('access_token')
	access_token_secret = request.args.get('access_token_secret')
	cred = {}
	session_id = 1

	f = open("guest_credentials_2.txt")
	for line in f:
	    name, value = line.split(":")
	    cred[name] = value.strip()
	f.close()

	cred['token'] = access_token
	cred['token_secret'] = access_token_secret

	'''	auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
	auth.set_access_token(cred["token"], cred["token_secret"])
	api = tweepy.API(auth)

	countt = 20

	public_tweets = api.home_timeline(count=countt,tweet_mode='extended')
	'''
	oauth = OAuth1Session(cred['key'],
                       client_secret=cred['key_secret'],
                       resource_owner_key=cred['token'],
                       resource_owner_secret=cred['token_secret'])
	#response = oauth.get("https://api.twitter.com/labs/2/tweets", params = params)
	params = {"count": "20","tweet_mode": "extended"}
	response = oauth.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params = params)
	public_tweets = json.loads(response.text)
	#print(tweets)
	if public_tweets == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
		print("Rate limit exceeded.")
#	fileList = glob.glob("../post_pictures/*.jpg")
#	fileList_actor = glob.glob("../profile_pictures/*.jpg")

#	for file in fileList:
#		os.remove(file)

#	for file in fileList_actor:
#		os.remove(file)
	#dbwrite = access_object.access_object() # This might be the wrong syntax dont recall.
	feed_json = []
	i = 1
	for tweet in public_tweets:
		# Checking for an image in the tweet. Adds all the links of any media type to the eimage list. 

		actor_name = tweet["user"]["name"]
		#tweet_id = str(tweet.id)
		dictToSend = {'tweet_id':tweet["id"]}
		requests.post('http://127.0.0.1:5052/insert_tweet?tweet_id='+str(tweet["id"]))
		#requests.post('http://127.0.0.1:5052/insert_tweet_session?fav_before='+str(tweet['favorited'])+'&sid='+str(session_id)+'&tid='+str(tweet["id"])+'&rtbefore='+str(tweet['retweeted'])+'&rank='+str(i))
		#print("Response : ")sid
		#print(res)

		full_text = tweet["full_text"]
		isRetweet = False 
		retweeted_by = ""
		actor_picture = tweet["user"]["profile_image_url"]
		actor_username = tweet["user"]["screen_name"]
		tempLikes = tweet["favorite_count"]
		try:
			full_text = tweet["retweeted_status"]["full_text"]
			retweeted_by = actor_name # Grab it here before changing the name
			actor_name = tweet["retweeted_status"]["user"]["name"] # original tweeter info used below.
			actor_username = tweet["retweeted_status"]["user"]["screen_name"]
			actor_picture = tweet["retweeted_status"]["user"]["profile_image_url"]
			tempLikes = tweet["retweeted_status"]["favorite_count"]
			isRetweet = True
		except:
			isRetweet = False
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
		if isRetweet:
			entities_keys = tweet["retweeted_status"]["entities"].keys()
			mediaArr = tweet["retweeted_status"]['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["retweeted_status"]["entities"]["urls"]
		else:
			entities_keys = tweet["entities"].keys()
			mediaArr = tweet['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["entities"]["urls"]
			# Redesigned block to retrieve the Cardinfo data.
		if "urls" in entities_keys:
			for each_url in all_urls:
				urls_list.append(each_url["url"])
				expanded_urls_list.append(each_url["expanded_url"])
			urls = ",".join(urls_list)
			expanded_urls = ",".join(expanded_urls_list)
		if len(expanded_urls_list) > 0:
			card_url = expanded_urls_list[0]
			card_data = Cardinfo.getCardData(card_url)
			if "image" in card_data.keys():
				image_raw = card_data['image']
				picture_heading = card_data["title"]
				picture_description = card_data["description"]



		# Embedded image retrieval (edited to handle retweets also now)

		eimage = []
		try: # Not sure why this has an issue all of a sudden.
			flag_image = False   
			if len(mediaArr) > 0:    
				for x in range(len(mediaArr)):
					if mediaArr[x]['type'] == 'photo':
						eimage.append(mediaArr[x]['media_url'])
						flag_image = True   
			if not flag_image:
				eimage.append("") 
		except Exception as error:
			print(error)
			eimage[0] = ""

		#if isRetweet:
			#print("Is a retweet.")

		for urll in urls_list:
			full_text = full_text.replace(urll,"")
		#print(full_text)
		full_text = xml.sax.saxutils.unescape(full_text)

		body = full_text
		date_string_temp = tweet['created_at'].split()
		date_string = date_string_temp[1] + " " + date_string_temp[2] + " " + date_string_temp[3] + " " + date_string_temp[5]
		td = (datetime.datetime.now() - datetime.datetime.strptime(date_string,"%b %d %H:%M:%S %Y"))
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
		#print("PROFILE LINK: " + tweet["user"]["url"])
		
		feed = {
			'body':body,
			'likes': finalLikes,
			'urls':urls,
			'expanded_urls':expanded_urls,
			'experiment_group':'var1',
			'post_id':i,
			'tweet_id':str(tweet["id"]),
			'class':'cohort', # Can we remove this from the pipeline to save the amount of data transferred slightly?
			'picture':image_raw,
			'picture_heading':picture_heading,
			'picture_description':picture_description,
			'actor_name':actor_name,
			'actor_picture': actor_picture,
			'actor_username': actor_username,
			'time':time,
			'embedded_image': eimage[0],
			'retweet_count': finalRetweets,
			'profile_link': profile_link,
			'retweet_by': retweeted_by
		}
		feed_json.append(feed)
		i = i + 1

	return jsonify(feed_json) # What is this doing?? Is this where we are sending the json of our feed_json to the other script?

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    app.run(host = "127.0.0.1", port = 5051)