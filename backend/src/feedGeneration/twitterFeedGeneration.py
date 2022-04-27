""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
import os
import re
import numpy as np
import datetime
import json
import src.feedGeneration.CardInfo as Cardinfo
import requests
from flask import Flask, render_template, request, url_for, jsonify
from collections import defaultdict
from requests_oauthlib import OAuth1Session
from configparser import ConfigParser
import xml
import xml.sax.saxutils
import src.feedGeneration.ranking as ranking

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

@app.route('/getfeed', methods=['GET'])
def get_feed():
	#Experimental code, need to make this so I can get the package back from the request, also need to add cookie checking here eventually.
	access_token = request.args.get('access_token')
	access_token_secret = request.args.get('access_token_secret')
	attn = int(request.args.get('attn'))
	page = int(request.args.get('page'))
	cred = config('../configuration/config.ini','twitterapp')
	cred['token'] = access_token.strip()
	cred['token_secret'] = access_token_secret.strip()
	oauth = OAuth1Session(cred['key'],
						client_secret=cred['key_secret'],
						resource_owner_key=cred['token'],
						resource_owner_secret=cred['token_secret'])
	public_tweets = None
	worker_id = request.args.get('worker_id')
	refresh = 0
	new_session = False
	if attn == 0 and page == 0:
		new_session = True
		params = {"count": "80","tweet_mode": "extended"}
		response = oauth.get("https://api.twitter.com/1.1/statuses/home_timeline.json", params = params)
		public_tweets = json.loads(response.text)
		tot_tweets = len(public_tweets)
		if public_tweets == "{'errors': [{'message': 'Rate limit exceeded', 'code': 88}]}":
			print("Rate limit exceeded.")
		db_tweet_payload = []
		db_tweet_session_payload = []
		db_tweet_attn_payload = []
		rankk = 0
		tweetids_by_page = defaultdict(list)
		all_tweet_ids = [tweet['id'] for tweet in public_tweets] #######
		if len(all_tweet_ids) == len(set(all_tweet_ids)):
			print("No duplicate tweets found")
		else:
			print("Duplicate tweets found")
		# tweets_with_ng = []
		for tweet in public_tweets:
			# is_newsguard = False
			# tweet_rank = None
			# if "entities" in tweet.keys():
			# 	if "urls" in tweet["entities"]:
			# 		for url_dict in tweet["entities"]["urls"]:
			# 			if is_newsguard == False:
			# 				is_newsguard = ranking.ngCheck(url_dict)
			# tweets_with_ng.append((tweet, is_newsguard)) # append tweet with ranking to structure
			# print("Tweet NG Status: " + str(is_newsguard))
			# print("")
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
		# ranking.tweetRank(tweets_with_ng) # send tweet structure with rankings to ranking function
		for attn_page in range(5):
			present_tweets = tweetids_by_page[attn_page]
			absent_tweets = all_tweet_ids[(attn_page+1)*10+1:]
			present_tweets_select = np.random.choice(present_tweets,size=3,replace=False)
			absent_tweets_select = np.random.choice(absent_tweets,size=2,replace=False)
			all_attn_tweets = np.concatenate((present_tweets_select,absent_tweets_select),axis=0)
			np.random.shuffle(all_attn_tweets)
			for tt in all_attn_tweets:
				db_tweet_attn = {
					'tweet_id':str(tt),
					'page':str(attn_page)
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
			public_tweets = [d[4] for d in db_response]
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
		is_newsguard = False
		tweet_rank = None
		if "entities" in tweet.keys():
			if "urls" in tweet["entities"]:
				for url_dict in tweet["entities"]["urls"]:
					url_start.append(url_dict["indices"][0])
					url_end.append(url_dict["indices"][1])
					url_display.append(url_dict["display_url"])
					url_extend.append(url_dict["expanded_url"])
					url_actual.append(url_dict["url"])
					if is_newsguard == False:
						is_newsguard = ranking.ngCheck(url_dict)
		print("Tweet NG Status: " + str(is_newsguard))
		print("")

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
			'user_retweet': str(tweet['retweeted']),
			'user_fav': str(tweet['favorited']),
			'retweet_by': retweeted_by,
			'quoted_by': quoted_by,
			'quoted_by_text' : quoted_by_text,
			'quoted_by_actor_username' : quoted_by_actor_username,
			'quoted_by_actor_picture' : quoted_by_actor_picture,
			'is_newsguard' : is_newsguard,
			'tweet_rank' : tweet_rank
		}
		feed_json.append(feed)
		rankk = rankk + 1
	ranking.tweetRank(feed_json) # call ranking function here and send feed_json?
	return jsonify(feed_json)

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5051)