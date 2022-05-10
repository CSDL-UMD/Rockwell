import json
import requests
import random
import math

# from requests.adapters import HTTPAdapter #??
# from requests.packages.urllib3.util.retry import Retry #??

# ng_tweets = []
# non_ng_tweets = []

with open('..\eligibility\Resources\domains.json', 'r') as ngdomains:
	domain_list = json.load(ngdomains)

#Splits dictionary of tweets into newsGuard tweets and non newsGuard tweets
def ngCheck(public_tweets):
    count = 0
    ng_tweets = []
    non_ng_tweets = []
    for tweet in public_tweets:
        is_newsguard = False
        if "entities" in tweet.keys():
            if "urls" in tweet["entities"]:
                ngLink = ""
                for url_dict in tweet["entities"]["urls"]:
                    # session = requests.Session() #??
                    # retry = Retry(connect=3, backoff_factor=0.5) #??
                    # adapter = HTTPAdapter(max_retries=retry) #??
                    # session.mount('http://', adapter) #??
                    # session.mount('https://', adapter) #??
                    h = requests.head(url_dict["expanded_url"], allow_redirects=True) #?? (Replace requests with session)
                    for each_ng_domain in domain_list["Domains"]:
                        if each_ng_domain in h.url:
                            ngLink = each_ng_domain
                            is_newsguard = True
                    print(str(is_newsguard) + " " + ngLink + " " + h.url + "\n")
        if is_newsguard == True:
            ng_tweets.append(tweet)
        else:
            non_ng_tweets.append(tweet)
    print("Ranking count: " + str(count))
    return ng_tweets, non_ng_tweets


def tweetRank():
    return round(random.uniform(0, 1), 2)


def pageArrangement(ng_tweets, non_ng_tweets):
    ranked_ng_tweets = []
    final_resultant_feed = []
    resultant_feed = [None] * 50
    pt = len(ng_tweets) / (len(non_ng_tweets) + len(non_ng_tweets))

    #We do not want more than 50% NewsGuard tweets on the feed
    if pt > 0.5:
        pt = 0.5

    #Rank the NG tweets
    for tweet in ng_tweets:
        rank = tweetRank()
        ranked_ng_tweets.append((tweet, rank))
    
    #Top 50 tweets from NewsGuard
    ranked_ng_tweets.sort(key=lambda a: a[1], reverse=True)
    selection_threshold_rnk = 50 * pt
    top_50 = [None] * math.ceil(selection_threshold_rnk) #ranked_ng_tweets[0:selection_threshold_rnk]
    for i in range(len(top_50)):
        top_50[i] = ranked_ng_tweets[i]

    #50 other tweets
    selection_threshold = 50 * (1 - pt)
    other_tweets = non_ng_tweets[0:math.floor(selection_threshold)]

    #Assign positions in feed to the NG and non NG tweets
    for i in range(len(resultant_feed)):
        chance = random.randint(1, 100)
        if chance < (pt * 100):
            if len(top_50) != 0:
                resultant_feed[i] = top_50[0][0]
                top_50.pop(0)
        else:
            if len(other_tweets) != 0:
                resultant_feed[i] = other_tweets[0]
                other_tweets.pop(0)

    for tweet in resultant_feed:
        if tweet != None:
            final_resultant_feed.append(tweet)

    return final_resultant_feed


# def tweetRank(tweets):
#     ng_tweets = []
#     non_ng_tweets = []
#     ng_count = 0
#     non_ng_count = 0
#     for tweet in tweets:
#         if tweet["is_newsguard"] == True:
#             ng_count = ng_count + 1
#             tweet["tweet_rank"] = round(random.uniform(0, 1), 2)
#             print("This is a NG tweet and its ranking is " + str(tweet["tweet_rank"]))
#             ng_tweets.append(tweet)
#         else:
#             non_ng_count = non_ng_count + 1
#             non_ng_tweets.append(tweet)
        
    
    # pt = ng_count / (non_ng_count + ng_count)
    # if pt > 0.5:
    #     pt = 0.5

    


    # query = url_dict["expanded_url"]
    # h = requests.head(query, allow_redirects=True)
    # while h.status_code == 200:
    #     for each_ng_domain in domain_list["Domains"]:
    #         if each_ng_domain in h:
    #             result = True
    #             return result
    #         else:
    #             h = requests.head(h.url, allow_redirects=True)
    # return result
    
    
    
    # result = False
    # ngLink = ""
    # link = url_dict["expanded_url"]
    # for each_ng_domain in domain_list["Domains"]:
    #     if each_ng_domain in url_dict["expanded_url"]: #if url_dict["expanded_url"].rfind(each_ng_domain) != -1: ????
    #         #print("NG Domain: " +str(each_ng_domain))
    #         #print("Expanded URL: " + str(url_dict["expanded_url"]))
    #         result = True
    #         ngLink = each_ng_domain
    #         break
    # # print("NG Domain: " +str(each_ng_domain))
    # # print("Expanded URL: " + str(url_dict["expanded_url"]))
    # print(str(result) + " " + ngLink + " " + link)
    # return result
    
    
    
    
    # result = False
    # r = requests.get(url_dict["expanded_url"])
    # print(r.history)
    # for x in r.history:
    #     # print(x.url)
    #     for each_ng_domain in domain_list["Domains"]:
    #         # print("NG Domain: " +str(each_ng_domain))
    #         # print("Expanded URL: " + str(x.url))
    #         if each_ng_domain in x.url:
    #             result = True
    #             return result
    # return result
    
    
    # query = url_dict["expanded_url"]
    # h = requests.head(query, allow_redirects=True)
    # while h.status_code == 200:
    #     for each_ng_domain in domain_list["Domains"]:
    #         if each_ng_domain in h:
    #             result = True
    #             return result
    #         else:
    #             h = requests.head(h.url, allow_redirects=True)
    # return result


    # #print("NG Domain: " +str(each_ng_domain))
    # #print("Expanded URL: " + str(url_dict["expanded_url"]))
    # #print(str(result) + " " + ngLink + " " + link)
    # return result


# def ngCheck(url_dict): 
#     result = False
#     h = requests.head(url_dict["expanded_url"], allow_redirects=True) #requests.get returns final link after all redirects (why not use this?)
#     ngLink = ""
#     for each_ng_domain in domain_list["Domains"]:
#         if each_ng_domain in h.url:
#             result = True
#             ngLink = each_ng_domain
#             break
#     print(str(result) + " " + ngLink + " " + h.url)
#     return result