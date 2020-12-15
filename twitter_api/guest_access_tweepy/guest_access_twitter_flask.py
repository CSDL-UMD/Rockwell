""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
import os
import random
import string
import glob
import tweepy
import pandas as pd
import datetime
import json
import Cardinfo
import TweetObject
from flask import Flask, render_template, request, url_for, jsonify
import requests as rq

app = Flask(__name__)

app.debug = False

@app.route('/getfeed/', methods=['GET'])
def get_feed():

	cred = {}

	f = open("../twauth-web-master/guest_credentials.txt")
	for line in f:
	    name, value = line.split(":")
	    cred[name] = value.strip()
	f.close()

	auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
	auth.set_access_token(cred["token"], cred["token_secret"])
	api = tweepy.API(auth)

	countt = 20

	public_tweets = api.home_timeline(count=countt,tweet_mode='extended')

	i = 1
	"""
	idd = []
	tweet_id = []
	body = []
	picture = []
	picture_heading = []
	picture_description = []
	actor = []
	likes = []
	expanded_urls = []
	urls = []
	time = []
	classs = ["cohort"]*countt
	experiment_group = ["var1"]*countt
	post_name = []
	post_handle = []
	post_photo = []
	"""

	fileList = glob.glob("/home/saumya/Documents/USF/Project/ASD/truman/truman_infodiversity/post_pictures/*.jpg")
	fileList_actor = glob.glob("/home/saumya/Documents/USF/Project/ASD/truman/truman_infodiversity/profile_pictures/*.jpg")

	for file in fileList:
		os.remove(file)

	for file in fileList_actor:
		os.remove(file)

	feed_json = []

	for tweet in public_tweets:
		print(i)
		actor_profile_pic = rq.get(tweet.user.profile_image_url)
		random_string_actor_pic = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
		actor_test = open("/home/saumya/Documents/USF/Project/ASD/truman/truman_infodiversity/profile_pictures/"+random_string_actor_pic+".jpg","wb")
		actor_test.write(actor_profile_pic.content)
		actor_picture = random_string_actor_pic+'.jpg'
		actor_name = tweet.user.name
		actor_handle = tweet.user.screen_name
		tweet_id = str(tweet.id)
		likes = tweet.favorite_count
		entities_keys = tweet.entities.keys()
		urls_list = []
		expanded_urls_list = []
		urls = ""
		expanded_urls = ""
		picture = ""
		picture_heading = ""
		picture_description = ""
		if "urls" in entities_keys:
			all_urls = tweet.entities["urls"]
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
				random_string_card_pic = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
				test = open("/home/saumya/Documents/USF/Project/ASD/truman/truman_infodiversity/post_pictures/"+random_string_card_pic+".jpg","wb")
				test.write(image_raw.content)
				picture = random_string_card_pic+".jpg"
				picture_heading = card_data["title"]
				picture_description = card_data["description"]
		full_text = tweet.full_text
		#url_idx = full_text.index(urls_list[0])
		#starting_para = full_text[:url_idx]
		#url_para = full_text[url_idx:url_idx+len(urls_list[0])]
		#end_para = full_text[url_idx+len(urls_list[0]):]
		#full_text = full_text.replace(starting_para,"#["+starting_para+"]")
		#full_text = full_text.replace(url_para,"#[a(href=\""+url_para+"\")"+url_para+"]")
		#full_text = full_text.replace(end_para,"#["+end_para+"]")
		#print(full_text)
		#full_text = full_text.replace(starting_para,"#["+starting_para+"]")
		for urll in urls_list:
		#	full_text = full_text.replace(urll,"<a href=\""+urll+"\")"+urll+"</a>")
			#full_text = full_text.replace(urll,"#[a(href=\""+urll+"\")"+urll+"]")
			#full_text = full_text.replace(urll,"<l>"+urll+"<l>")
			full_text = full_text.replace(urll,"")
		#full_text = "!{t('" + full_text + "')}"
		#print(full_text)
		body = full_text
		td = (datetime.datetime.now() - tweet.created_at)
		hours, remainder = divmod(td.seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		time = ""
		if minutes < 10:
			time = "-00:0"+str(minutes)
		else:
			time = "-00:"+str(minutes)
		#time.append(td.seconds)

		feed = {
			'body':body,
			'likes':likes,
			'urls':urls,
			'expanded_urls':expanded_urls,
			'experiment_group':'var1',
			'post_id':i,
			'tweet_id':tweet_id,
			'class':'cohort',
			'picture':picture,
			'picture_heading':picture_heading,
			'picture_description':picture_description,
			'actor_name':actor_name,
			'actor_picture':actor_picture,
			'actor_username':actor_handle,
			'time':time
		}
		feed_json.append(feed)
		i = i + 1
	"""
	tweet_collections = []
	for i in range(len(idd)):
		tweet_object = TweetObject.TweetObject(urls[i],expanded_urls[i],experiment_group[i],idd[i],tweet_id[i],body[i],classs[i],picture[i],picture_heading[i],picture_description[i],actor[i],time[i],post_name[i],post_handle[i],post_photo[i])
		tweet_collections.append(tweet_object)
	feed_json = []
	for i in range(len(idd)):
		feed_json.append(ob.__dict__ for ob in tweet_collections)	
	"""
	#out = json.dumps([ob.__dict__ for ob in tweet_collections], indent = 1)
	#out = '###'.join([jsonify(ob.__dict__) for ob in tweet_collections])
	#print(feed_json)
	return jsonify(feed_json)
	#return jsonify({'feed':feed_json})
	#print("Saumya Bhadani : "+out)
	#sys.stdout.flush()

	"""
	writeOut = open("data.json","w")
	writeOut.write(out)
	
	pd_all = pd.concat([pd.DataFrame(idd),pd.DataFrame(tweet_id),pd.DataFrame(body),pd.DataFrame(picture),pd.DataFrame(likes),pd.DataFrame(urls),pd.DataFrame(expanded_urls),pd.DataFrame(actor),pd.DataFrame(picture),pd.DataFrame(picture_heading),pd.DataFrame(picture_description),pd.DataFrame(time),pd.DataFrame(classs),pd.DataFrame(experiment_group)],axis=1)
	pd_all.columns = ["id","tweet_id","body","picture","likes","urls","expanded_urls","actor","pictures","pictures_title","pictures_description","time","class","experiment_group"]
	pd_all.to_csv("../../truman/truman_infodiversity/input/posts_twitter_demo.csv",encoding='utf-8', index=False)
	"""

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    app.run(host = "127.0.0.1", port = 5051)