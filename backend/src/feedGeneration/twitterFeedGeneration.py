""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
import os
import re
import numpy as np
import datetime
import json
import random, string
import CardInfo as Cardinfo
import requests
from flask import Flask, render_template, request, url_for, jsonify
from collections import defaultdict
from requests_oauthlib import OAuth1Session
from configparser import ConfigParser
import xml
import xml.sax.saxutils

#import requests as rq

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

session_id_store = {}

@app.route('/getfeed', methods=['GET'])
def get_feed():
	worker_id = str(request.args.get('worker_id')).strip()
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
		for attn_tweet in db_response_attn:
			db_tweet = {
				'tweet_id': attn_tweet[0],
				'page' : attn_tweet[2],
				'attn' : attn_tweet[3],
				'present' : attn_tweet[1]
			}
			attn_payload.append(db_tweet)
		timeline_payload = []
		for timeline_tweet in db_response_timeline:
			db_tweet = {
				'fav_before': timeline_tweet[2],
				'tid' : timeline_tweet[0],
				'rtbefore' : timeline_tweet[3],
				'page' : timeline_tweet[4],
				'rank' : timeline_tweet[5]
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
		db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_new?worker_id='+str(worker_id)+"&page="+str(page)+"&feedtype="+feedtype)
		db_response = db_response.json()['data']
		public_tweets = [d[4] for d in db_response]

	feed_json = []
	rankk = 1

	for tweet in public_tweets: # Modify what tweet is for this loop in order to change the logic ot use our data or twitters.

		# Checking for an image in the tweet. Adds all the links of any media type to the eimage list.
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
			entities_keys = tweet["retweeted_status"]["quoted_status"]["entities"].keys()
			mediaArr = tweet["retweeted_status"]["quoted_status"]['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["retweeted_status"]["quoted_status"]["entities"]["urls"]
		elif isQuote: #  quote only case
			entities_keys = tweet["quoted_status"]["entities"].keys()
			mediaArr = tweet["quoted_status"]['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["quoted_status"]["entities"]["urls"]
		elif isRetweet:
			entities_keys = tweet["retweeted_status"]["entities"].keys()
			mediaArr = tweet["retweeted_status"]['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["retweeted_status"]["entities"]["urls"]
		else:
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


			# Redesigned block to retrieve the Cardinfo data.
		if "urls" in entities_keys and not hasEmbed:
			for each_url in all_urls:
				urls_list.append(each_url["url"])
				expanded_urls_list.append(each_url["expanded_url"])
			urls = ",".join(urls_list)
			expanded_urls = ",".join(expanded_urls_list)
		if len(expanded_urls_list) > 0 and not isQuote and not hasEmbed: # not isQuote is to save time in the case of a quote. no card needed
			card_url = expanded_urls_list[0]
			card_data = Cardinfo.getCardData(card_url)
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
	last_feed_value = {'session_id' : session_id}
	feed_json.append(last_feed_value)
	return jsonify(feed_json)

@app.route('/getfeedprev', methods=['GET'])
def get_feed_prev():
	#Experimental code, need to make this so I can get the package back from the request, also need to add cookie checking here eventually.
	random_indentifier = request.args.get('random_indentifier')
	access_token = access_token_store[random_indentifier]
	access_token_secret = access_token_secret_store[random_indentifier]
	#access_token = request.args.get('access_token')
	#access_token_secret = request.args.get('access_token_secret')
	attn = int(request.args.get('attn'))
	page = int(request.args.get('page'))
	feedtype = str(request.args.get('feedtype')).strip()
	screen_name = screenname_store[random_indentifier]
	user_id = userid_store[random_indentifier]
	#screen_name = request.args.get('screen_name')
	#user_id = request.args.get('user_id')
	cred = config('../configuration/config.ini','twitterapp')
	cred['token'] = access_token.strip()
	cred['token_secret'] = access_token_secret.strip()
	oauth = OAuth1Session(cred['key'],
						client_secret=cred['key_secret'],
						resource_owner_key=cred['token'],
						resource_owner_secret=cred['token_secret'])
	public_tweets = None
	worker_id = worker_id_store[random_indentifier]
	#worker_id = request.args.get('worker_id')
	print("Worker Id in Twitter feed generation : "+str(worker_id))
	print("Attention : "+str(attn)+" Page : "+str(page))
	refresh = 0
	new_session = False
	if attn == 0 and page == 0:
		new_session = True
		params = {"count": "80","tweet_mode": "extended"}
		response = oauth.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params = params)
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
		public_tweets = public_tweets[0:10]
	else:
		if attn == 1:
			db_response = requests.get('http://127.0.0.1:5052/get_existing_attn_tweets?worker_id='+str(worker_id)+"&page="+str(page))
			db_response = db_response.json()['data']
			public_tweets = [d[1] for d in db_response]
		else:	
			db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets?worker_id='+str(worker_id)+"&page="+str(page)) # This definetely doesnt work right now.
			db_response = db_response.json()['data']
			public_tweets = [d[1] for d in db_response]
	"""
	This is for refresh
	if data_db != 'NEW':
		tweet_ids = [d[0] for d in data_db]
		min_ids = [d[1] for d in data_db]
		max_ids = [d[2] for d in data_db]
		refresh = data_db[0][3] + 1
		max_tweet_id = tweet_ids[max_ids.index(True)]
		min_tweet_id = tweet_ids[min_ids.index(True)]
		params = {"since_id": str(min_tweet_id-1),"tweet_mode": "extended"}
		response = oauth.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params = params)
		all_tweets = json.loads(response.text)
		new_tweet_ids = []
		for tweet in all_tweets:
			new_tweet_ids.append(tweet["id"])
		deleted_tweet_ids = list(set(tweet_ids) - set(new_tweet_ids))
		deleted_tweet_payload = []
		for del_tweet in deleted_tweet_ids:
			deleted_tweet_payload.append({'del_tweet':str(del_tweet)})
		if deleted_tweet_payload:
			requests.post('http://127.0.0.1:5052/set_deleted_tweets',json=deleted_tweet_payload)
		public_tweets = all_tweets[:20]
	"""
	feed_json = []
	rankk = 1

	for tweet in public_tweets: # Modify what tweet is for this loop in order to change the logic ot use our data or twitters.

		# Checking for an image in the tweet. Adds all the links of any media type to the eimage list.
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
			entities_keys = tweet["retweeted_status"]["quoted_status"]["entities"].keys()
			mediaArr = tweet["retweeted_status"]["quoted_status"]['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["retweeted_status"]["quoted_status"]["entities"]["urls"]
		elif isQuote: #  quote only case
			entities_keys = tweet["quoted_status"]["entities"].keys()
			mediaArr = tweet["quoted_status"]['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["quoted_status"]["entities"]["urls"]
		elif isRetweet:
			entities_keys = tweet["retweeted_status"]["entities"].keys()
			mediaArr = tweet["retweeted_status"]['entities'].get('media',[])
			if "urls" in entities_keys:
				all_urls = tweet["retweeted_status"]["entities"]["urls"]
		else:
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


			# Redesigned block to retrieve the Cardinfo data.
		if "urls" in entities_keys and not hasEmbed:
			for each_url in all_urls:
				urls_list.append(each_url["url"])
				expanded_urls_list.append(each_url["expanded_url"])
			urls = ",".join(urls_list)
			expanded_urls = ",".join(expanded_urls_list)
		if len(expanded_urls_list) > 0 and not isQuote and not hasEmbed: # not isQuote is to save time in the case of a quote. no card needed
			card_url = expanded_urls_list[0]
			card_data = Cardinfo.getCardData(card_url)
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
			'refreshh':str(refresh),
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
	new_random_identifier_len = random.randint(15, 26)
	new_random_identifier = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(new_random_identifier_len))
	screenname_store[new_random_identifier] = screen_name
	userid_store[new_random_identifier] = user_id
	worker_id_store[new_random_identifier] = worker_id
	access_token_store[new_random_identifier] = access_token
	access_token_secret_store[new_random_identifier] = access_token_secret
	del screenname_store[random_indentifier]
	del userid_store[random_indentifier]
	del worker_id_store[random_indentifier]
	del access_token_store[random_indentifier]
	del access_token_secret_store[random_indentifier]
	set_user_credentials_payload_db = {'worker_id': str(worker_id), 'random_indentifier': new_random_identifier}
	requests.post('http://127.0.0.1:5052/set_credentials',params=set_user_credentials_payload_db)
	last_feed_value = {'new_random_identifier' : new_random_identifier}
	feed_json.append(last_feed_value)
	return jsonify(feed_json)

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5054)
