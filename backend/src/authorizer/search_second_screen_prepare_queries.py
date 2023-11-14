import re
import json
import gzip
import pandas as pd

proj_dir = "/home/saumya/Documents/Infodiversity/Rockwell/backend/src"

def gettwitterhandle(url):
    try:
        return url.split("/")[3]
    except:
        return ""


def addtwitterNG(df):
    return (df.assign(twitter=df.twitter.apply(gettwitterhandle)))

def build_queries(twitter_list):
    queries = []
    query = ''
    for i in range(len(twitter_list)):
        if not query:
            query = 'from:'+twitter_list[i]
        else:
            if len(query + ' OR from:'+twitter_list[i]) < 512:
                query = query + ' OR from:'+twitter_list[i]
            else:
                queries.append(query)
                query = 'from:'+twitter_list[i]
    queries.append(query)
    return queries

ng_fn = proj_dir + "/recsys/NewsGuardIffy/label-2022101916.json"

with open(ng_fn) as f:
    obj = json.load(f)
d = {
    "identifier": [elem["identifier"] for elem in filter(None, obj) if re.match("en", elem["locale"])],
    "rank": [elem["rank"] for elem in filter(None, obj) if re.match("en", elem["locale"])],
    "score": [elem["score"] for elem in filter(None, obj) if re.match("en", elem["locale"])],
    "twitter": [elem['metadata'].get("TWITTER", {"body": ""})["body"] for elem in filter(None, obj) if re.match("en", elem["locale"])]
}
ng_domains = pd.DataFrame(d)
ng_domains = addtwitterNG(ng_domains)
ng_domains = ng_domains.rename(columns={"identifier": "domain"})

ng_domains_trustworthy = ng_domains[ng_domains["rank"] == "T"]
ng_domains_non_trustworthy = ng_domains[ng_domains["rank"] == "N"]

twitter_trustworthy = ng_domains_trustworthy['twitter'].unique().tolist()
twitter_trustworthy = [xx for xx in twitter_trustworthy if len(xx) > 0]

twitter_untrustworthy = ng_domains_non_trustworthy['twitter'].unique().tolist()
twitter_untrustworthy = [xx for xx in twitter_untrustworthy if len(xx) > 0]

queries_trustworthy = build_queries(twitter_trustworthy)
queries_untrustworthy = build_queries(twitter_untrustworthy)
file_num = 1

for qq in queries_trustworthy:
    writeObj = {
            "query" : qq,
            "newest_id" : 0,
            "oldest_id" : 0,
            "count" : 0,
            "next_token" : "NA",
            "NG_rank": "T",
            "data" : [],
            "error" : "NA"
        }
    with gzip.open("/home/saumya/Documents/Infodiversity/search_second_screen_data/query_{}.json.gz".format(file_num),'w') as outfile:
        outfile.write(json.dumps(writeObj).encode('utf-8'))
    file_num = file_num + 1

for qq in queries_untrustworthy:
    writeObj = {
            "query" : qq,
            "newest_id" : 0,
            "oldest_id" : 0,
            "count" : 0,
            "next_token" : "NA",
            "NG_rank" : "NT",
            "data" : [],
            "error" : "NA"
        }
    with gzip.open("/home/saumya/Documents/Infodiversity/search_second_screen_data/query_{}.json.gz".format(file_num),'w') as outfile:
        outfile.write(json.dumps(writeObj).encode('utf-8'))
    file_num = file_num + 1