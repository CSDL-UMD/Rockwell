import json
import requests

from requests import request

ng_tweets = []
non_ng_tweets = []

with open('..\eligibility\Resources\domains.json', 'r') as ngdomains:
	domain_list = json.load(ngdomains)

#Splits dictionary of tweets into newsGuard tweets and non newsGuard tweets
def ngCheck(url_dict): 
    result = False
    h = requests.head(url_dict["expanded_url"], allow_redirects=True) #requests.get returns final link after all redirects (why not use this?)
    ngLink = ""
    for each_ng_domain in domain_list["Domains"]:
        if each_ng_domain in h.url:
            result = True
            ngLink = each_ng_domain
            break
    print(str(result) + " " + ngLink + " " + h.url)
    return result


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
