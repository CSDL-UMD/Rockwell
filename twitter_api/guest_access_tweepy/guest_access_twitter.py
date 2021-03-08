""" Read the credentials from credentials.txt and place them into the `cred` dictionary """
import os
import glob
import tweepy
import pandas as pd
import datetime
import json
import Cardinfo
import TweetObject
import requests
from flask import jsonify

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

fileList = glob.glob("/home/saumya/Documents/USF/Project/ASD/truman/truman_infodiversity/post_pictures/card_image_*.jpg")

for file in fileList:
	os.remove(file)

for tweet in public_tweets:
	print(i)
	i = i + 1
	idd.append(i)
	tweet_id.append(str(tweet.id))
	dictToSend = {'tweet_id':tweet.id}
	res = requests.post('http://127.0.0.1:5052/insert_tweet/', json=dictToSend)
	print("Response : ")
	print(res)
	actor.append(tweet.user.screen_name)
	likes.append(tweet.favorite_count)
	entities_keys = list(tweet.entities.keys())
	urls_list = []
	expanded_urls_list = []
	if "urls" in entities_keys:
		all_urls = tweet.entities["urls"]
		for each_url in all_urls:
			urls_list.append(each_url["url"])
			expanded_urls_list.append(each_url["expanded_url"])
		urls.append(",".join(urls_list))
		expanded_urls.append(",".join(expanded_urls_list))

	else:
		urls.append("")
		expanded_urls.append("")
	if len(expanded_urls_list) > 0:
		card_url = expanded_urls_list[0]
		card_data = Cardinfo.getCardData(card_url)
		if "image" in card_data.keys():
			image_raw = card_data['image']
			test = open("/home/saumya/Documents/USF/Project/ASD/truman/truman_infodiversity/post_pictures/card_image_"+str(i)+".jpg","wb")
			test.write(image_raw.content)
			picture.append("card_image_"+str(i)+".jpg")
			picture_heading.append(card_data["title"])
			picture_description.append(card_data["description"])
		else:
			picture.append("")
			picture_heading.append("")
			picture_description.append("")
	else:
    		picture.append("")
    		picture_heading.append("")
    		picture_description.append("")
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
	body.append(full_text)
	td = (datetime.datetime.now() - tweet.created_at)
	hours, remainder = divmod(td.seconds, 3600)
	minutes, seconds = divmod(remainder, 60)
	if minutes < 10:
		time.append("-00:0"+str(minutes))
	else:
		time.append("-00:"+str(minutes))
	#time.append(td.seconds)

#pd_all = pd.concat([pd.DataFrame(idd),pd.DataFrame(tweet_id),pd.DataFrame(body),pd.DataFrame(picture),pd.DataFrame(likes),pd.DataFrame(urls),pd.DataFrame(expanded_urls),pd.DataFrame(actor),pd.DataFrame(picture),pd.DataFrame(picture_heading),pd.DataFrame(picture_description),pd.DataFrame(time),pd.DataFrame(classs),pd.DataFrame(experiment_group)],axis=1)
#pd_all.columns = ["id","tweet_id","body","picture","likes","urls","expanded_urls","actor","pictures","pictures_title","pictures_description","time","class","experiment_group"]
#pd_all.to_csv("../../truman/truman_infodiversity/input/posts_twitter_demo.csv",encoding='utf-8', index=False)