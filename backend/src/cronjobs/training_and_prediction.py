import re
import os
import math
import gzip
import json
import requests
import joblib
import numpy as np
import pandas as pd
import logging
import threading
import datetime
import surprise
import psycopg2
import random
import datetime
from collections import Counter
from dateutil import parser as date_parser
from collections import defaultdict
from configparser import ConfigParser
from multiprocessing import Manager
from multiprocessing.dummy import Pool
from argparse import ArgumentParser

LOG_FMT_DEFAULT='%(asctime)s:%(levelname)s:%(message)s'
LOG_PATH_DEFAULT="/home/rockwell/Rockwell/backend/src/cronjobs/prediction_cronjob.log"
diversity_file = '/home/rockwell/audience_diversity_2022-2023_visitor_level.csv'
alpha_m = 0.9
alpha_t = 0.1
datetime_eligibility = datetime.datetime(2023, 12, 1)

CF_STD_MEAN = 0.07970520315881752
CF_STD_SD = 0.15131052178146273
D_STD_MEAN = 0.39614151366977973
D_STD_SD = 0.37418325338955594

def config(filename='database.ini', section='postgresql'):
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

def get_hoaxy_engagement(user_id,hoaxy_config):

    """
    Returns a list of JSON that represents the tweets of the user inside the Hoaxy database.
    Args:
        user_id: The user ID of the user whose tweets you want to get.
    Returns:
        A list of JSON that represents the tweets of the user.
    """

    res = []
    hostname  = str(hoaxy_config['host'])
    port_id = str(hoaxy_config['port'])
    db = str(hoaxy_config['database'])
    username = str(hoaxy_config['user'])
    pwd = str(hoaxy_config['password'])
    conn = None
    cur = None

    err_message = "NA"

    try:
        conn = psycopg2.connect (
            host = hostname,
            dbname =db,
            user = username,
            password = pwd,
            port = port_id,
        )

        cur =  conn.cursor()
        script = """ select tweet.json_data from tweet join ass_tweet_url on tweet.id = ass_tweet_url.tweet_id join url on url.id = ass_tweet_url.url_id where user_id = placeholder; """

        script = script.replace("placeholder", str(user_id))
        cur.execute(script)


        for element in cur.fetchall():
            res.append(element[0])

    except Exception as err:
        err_message = err

    finally:
        if cur is not None:
            cur.close()

        if conn is not None:
            conn.close()
    return res,err_message

def make_logger(path=LOG_PATH_DEFAULT):
    """ 
    By default, log to file messages at level INFO or above. By default, the
    log file will be located in same location from where the script is being
    called. It also adds a stream handler for logging to the console messages
    at level ERROR and above; these will be logged to stderr.
    """
    logging.basicConfig(filename=path,
                        format=LOG_FMT_DEFAULT,
                        filemode='a',
                        level="INFO")
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter(LOG_FMT_DEFAULT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def make_parser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("proj_dir", help="main project directory")
    parser.add_argument("data_dir", help="directory with data files")
    return parser

def gettwitterhandle(url):
    try:
        return url.split("/")[3]
    except:
        return ""

def addtwitterNG(df):
    return (df.assign(twitter=df.twitter.apply(gettwitterhandle)))

def extractfromentities(payload):
    urls_extracted = []
    if "entities" in payload:
        entities = payload["entities"]
        for url_obj in entities["urls"]:
            urls_extracted.append(url_obj["expanded_url"])
        if "media" in entities:
            for media_obj in payload["entities"]["media"]:
                urls_extracted.append(media_obj["expanded_url"])
    if "extended_entities" in payload:
        for media_obj in payload["extended_entities"]["media"]:
            urls_extracted.append(media_obj["expanded_url"])
    return list(set(urls_extracted))

# by default cache results in memory
_CACHE = {}

def _newcache(fn=None):
    if fn is None:
        return dict()
    else:
        try:
            import dbhash
            return dbhash.open(fn, 'w')
        except ImportError:
            import sys
            print("warning: cannot import BerkeleyDB (dbhash), "
                  "storing cache in memory.",
                  file=sys.stderr)
            return dict()

def _setcache(fn=None):
    global _CACHE
    _CACHE = _newcache(fn)

def init(queue):
    global idx
    idx = queue.get()

def unshortenone(urlidx):
    global idx
    if urlidx[0] % 100 == 0:
        print(urlidx[0])
    u = urlidx[1]
    try:
        uk = u.encode('utf-8')
        if uk in _CACHE:
            return _CACHE[uk]
        r = requests.head(u, allow_redirects=True,timeout=10)
        _CACHE[uk] = r.url
        return r.url
    except Exception as e:
        return u

def unshorten(urls, threads=None, cachepath=None):
    """
    Iterator over unshortened versions of input URLs. Follows redirects using
    HEAD commands. Operates in parallel using multiple threads of execution.

    Parameters
    ==========

    urls : iterator
        a sequence of short URLs.

    threads : int
        optional; number of threads to use.

    cachepath : str
        optional; path to file with cache (for reuse). By default will use
        in-memory cache.
    """
    _setcache(cachepath)

    d = threading.local()
    def set_num(counter):
        d.id = next(counter) + 1

    ids = list(range(threads))
    manager = Manager()
    idQueue = manager.Queue()

    for i in ids:
        idQueue.put(i)

    pool = Pool(threads,init,(idQueue,))
    urlswithidx = [list(uidx) for uidx in zip(range(len(urls)),urls)]
    for url in pool.imap(unshortenone, urlswithidx):
        yield url

def integrate_NG_iffy(ng_fn,iffyfile):
    iffy_domains = pd.read_csv(iffyfile)['Domain'].values.tolist()
    ng_domains = pd.read_csv(ng_fn)
    ng_domains = ng_domains.loc[ng_domains['Rating'] != 'P'].reset_index(drop=True)
    ng_domains = ng_domains.loc[ng_domains['Rating'] != 'S'].reset_index(drop=True)    
    ng_domain_values = ng_domains['Domain'].values
    for iffy_domain in iffy_domains:
        if iffy_domain not in ng_domain_values:
            df_iffy = {'Domain':iffy_domain,'Parent_Domain':iffy_domain,'Twitter':'#!NA!#','Rating':'N','Score':-100}
            ng_domains = ng_domains.append(df_iffy,ignore_index=True)
    return ng_domains

def unshorten_and_tag_NG(all_urls,ng_domains):
    ng_domain_values = ng_domains['Domain'].unique()
    ng_twitter_values = ng_domains['Twitter'].unique()
    urls_unshorted = []
    outputs = unshorten(all_urls, threads=20, cachepath='/home/saumya/')
    for url in outputs:
        urls_unshorted.append(url)
    
    urls_domains = []
    urls_twitter = []
    urls_domains_display = []
    for url in urls_unshorted:
        domain = ".".join(url.split("/")[2].split(".")[-2:])
        urls_domains.append(domain)
        domain_display = ".".join(url.split("/")[2].split(".")[-3:])
        if 'www' in domain_display:
            domain_display = domain
        urls_domains_display.append(domain_display)
        if domain == "twitter.com":
            try:
                urls_twitter.append(url.split("/")[3])
            except:
                urls_twitter.append("NA")
        else:
            urls_twitter.append("NA")
    
    urls_tagged = []
    urls_rating = []
    urls_score = []
    for idx in range(len(urls_domains)):
        if urls_domains[idx] in ng_domain_values:
            rating_val = ng_domains.loc[(ng_domains['Domain'] == urls_domains[idx])]['Rating'].values[0]
            score_val = ng_domains.loc[(ng_domains['Domain'] == urls_domains[idx])]['Score'].values[0]
            urls_tagged.append(urls_domains[idx])
            urls_rating.append(rating_val)
            urls_score.append(score_val)
        elif urls_twitter[idx] != "NA":
            if urls_twitter[idx] in ng_twitter_values: 
                try:
                    twitter_domain = ng_domains.loc[(ng_domains['Twitter'] == urls_twitter[idx])]['Domain'].values[0]
                    rating_val = ng_domains.loc[(ng_domains['Domain'] == twitter_domain)]['Rating'].values[0]
                    score_val = ng_domains.loc[(ng_domains['Domain'] == twitter_domain)]['Score'].values[0]
                    urls_rating.append(rating_val)
                    urls_score.append(score_val)
                    urls_tagged.append(twitter_domain)
                except KeyError:
                    urls_tagged.append("NA")
                    urls_rating.append("Z")
                    urls_score.append(-1000)
                    continue
            else:
                urls_tagged.append("NA")
                urls_rating.append("Z")
                urls_score.append(-1000)
        else:
            urls_tagged.append("NA")
            urls_rating.append("Z")
            urls_score.append(-1000)
    return urls_tagged,urls_domains_display,urls_rating,urls_score

def tag_NG_handles(all_handles,ng_domains):
    ng_twitter_values = ng_domains['Twitter'].unique()
    handles_tagged = []
    for handle in all_handles:
        if handle in ng_twitter_values:
            corrs_domain = ng_domains.loc[(ng_domains['Twitter'] == handle)]['Domain'].values.tolist()
            actual_domain = 'NA'
            for dd in corrs_domain:
                if dd.count('.') == 1:
                    actual_domain = dd
                    break
            if actual_domain == 'NA':
                actual_domain = corrs_domain[0]
            handles_tagged.append(actual_domain)
        else:
            handles_tagged.append("NA")
    return handles_tagged

def idf(values,tot_users=0):
    num_users = len(set(values))
    return math.log10(tot_users/num_users)

def tfidf(values,idf_dict={}):
    domain_counter = Counter(values)
    domain_rating = {}
    for dd in domain_counter.keys():
        tf = domain_counter[dd]/len(values)
        idf = idf_dict[dd]
        domain_rating[dd] = tf/idf
    domain_rating_json = json.dumps(domain_rating, indent = 4)
    return domain_rating_json

def rating_calculate(values):
    domain_rating = {}
    total = len(values)
    if total == 1:
        domain_rating[values.tolist()[0]] = 1.0
    else:
        total_log = math.log10(total)
        domain_counter = Counter(values)
        for dd in domain_counter.keys():
            fracc = 0.1
            if domain_counter[dd] > 1:
                fracc = math.log10(domain_counter[dd])
            rating_log = float(fracc)/float(total_log)
            domain_rating[dd] = rating_log
    domain_rating_json = json.dumps(domain_rating, indent = 4)
    return domain_rating_json

def get_data_from_new_users(user_timeline_files,fave_timeline_files,ng_domains):

    users = []
    engaged_urls = []
    
    users_handles = []
    engaged_handles = []
    location_handles = []
    
    for fn in user_timeline_files:
        with gzip.open(fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            user_tweets = []
            if data['userTweets']:
                for user_tweet_arr in data['userTweets']:
                    if type(user_tweet_arr) is list:
                        user_tweets = user_tweets + user_tweet_arr
                    else:
                        user_tweets.append(user_tweet_arr)
            if user_tweets:
                user_id = data["userObject"]["screen_name"]
                for tweet in user_tweets:
                    if 'retweeted_status' in tweet:
                        users_handles.append(user_id)
                        engaged_handles.append(tweet['retweeted_status']['user']['screen_name'])
                        location_handles.append('retweet')
                        urls_extracted = extractfromentities(tweet['retweeted_status'])
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet['retweeted_status']:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['retweeted_status']['quoted_status']['user']['screen_name'])
                            location_handles.append('retweetofquote')
                            urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                    else:
                        if 'quoted_status' in tweet:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['quoted_status']['user']['screen_name'])
                            location_handles.append('quote')
                            urls_extracted = extractfromentities(tweet['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                        urls_extracted = extractfromentities(tweet)
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                            
    for fn in fave_timeline_files:
        with gzip.open(fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            liked_tweets = []
            if data['likedTweets']:
                for liked_tweets_arr in data['likedTweets']:
                    if type(liked_tweets_arr) is list:
                        liked_tweets = liked_tweets + liked_tweets_arr
                    else:
                        liked_tweets.append(liked_tweets_arr)
            if liked_tweets:
                user_id = data["userObject"]["screen_name"]
                for tweet in liked_tweets:
                    if 'retweeted_status' in tweet:
                        users_handles.append(user_id)
                        engaged_handles.append(tweet['retweeted_status']['user']['screen_name'])
                        location_handles.append('retweet')
                        urls_extracted = extractfromentities(tweet['retweeted_status'])
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet['retweeted_status']:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['retweeted_status']['quoted_status']['user']['screen_name'])
                            location_handles.append('retweetofquote')
                            urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                    else:
                        users_handles.append(user_id)
                        engaged_handles.append(tweet['user']['screen_name'])
                        location_handles.append('original')
                        urls_extracted = extractfromentities(tweet)
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['quoted_status']['user']['screen_name'])
                            location_handles.append('quote')
                            urls_extracted = extractfromentities(tweet['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
    
    engaged_urls_tagged = unshorten_and_tag_NG(engaged_urls,ng_domains)[0]
    engaged_handles_tagged = tag_NG_handles(engaged_handles,ng_domains)
    
    new_users_training = []
    new_domains_training = []
    
    new_users_handles_training = []
    new_handles_training = []
    
    for i in range(len(users)):
        if engaged_urls_tagged[i] != 'NA':
            new_users_training.append(users[i])
            new_domains_training.append(engaged_urls_tagged[i])

    for i in range(len(users_handles)):
        if engaged_handles_tagged[i] != 'NA':
            new_users_training.append(users_handles[i])
            new_domains_training.append(engaged_handles_tagged[i])
        else:
            if location_handles[i] == 'retweet' or location_handles[i] == 'quote':
                new_users_handles_training.append(users_handles[i])
                new_handles_training.append(engaged_handles[i])
    
    pd_new_users = pd.concat([pd.DataFrame(new_users_training,columns=['Users']),
                              pd.DataFrame(new_domains_training,columns=['Items'])],axis=1)
    
    pd_new_users_handles = pd.concat([pd.DataFrame(new_users_handles_training,columns=['Users']),
                              pd.DataFrame(new_handles_training,columns=['Items'])],axis=1)

    pd_new_users_both = pd.concat([pd_new_users,pd_new_users_handles])
    
    return pd_new_users_both

def get_data_from_hometimeline(tweet_list,user_id,ng_domains,screen):
    
    users = []
    engaged_urls = []
    tweet_id_urls = []
    age_urls = []
    
    users_handles = []
    engaged_handles = []
    tweet_id_handles = []
    age_handles = []
    
    for tweet in tweet_list:
        tweet_id = tweet['id']
        date_string_temp = tweet['created_at']
        created_date_datetime = date_parser.parse(date_string_temp)
        td = (datetime.datetime.now(datetime.timezone.utc) - created_date_datetime)
        age_seconds = td.seconds
        if 'retweeted_status' in tweet:
            users_handles.append(user_id)
            engaged_handles.append(tweet['retweeted_status']['user']['screen_name'])
            tweet_id_handles.append(tweet_id)
            age_handles.append(age_seconds)
            urls_extracted = extractfromentities(tweet['retweeted_status'])
            for url in urls_extracted:
                users.append(user_id)
                engaged_urls.append(url)
                tweet_id_urls.append(tweet_id)
                age_urls.append(age_seconds)
            if 'quoted_status' in tweet['retweeted_status']:
                users_handles.append(user_id)
                engaged_handles.append(tweet['retweeted_status']['quoted_status']['user']['screen_name'])
                tweet_id_handles.append(tweet_id)
                age_handles.append(age_seconds)
                urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                for url in urls_extracted:
                    users.append(user_id)
                    engaged_urls.append(url)
                    tweet_id_urls.append(tweet_id)
                    age_urls.append(age_seconds)
        else:
            users_handles.append(user_id)
            engaged_handles.append(tweet['user']['screen_name'])
            tweet_id_handles.append(tweet_id)
            age_handles.append(age_seconds)
            urls_extracted = extractfromentities(tweet)
            for url in urls_extracted:
                users.append(user_id)
                engaged_urls.append(url)
                tweet_id_urls.append(tweet_id)
                age_urls.append(age_seconds)
            if 'quoted_status' in tweet:
                users_handles.append(user_id)
                engaged_handles.append(tweet['quoted_status']['user']['screen_name'])
                tweet_id_handles.append(tweet_id)
                age_handles.append(age_seconds)
                urls_extracted = extractfromentities(tweet['quoted_status'])
                for url in urls_extracted:
                    users.append(user_id)
                    engaged_urls.append(url)
                    tweet_id_urls.append(tweet_id)
                    age_urls.append(age_seconds)
    
    engaged_urls_tagged,urls_domain,urls_rating,urls_score = unshorten_and_tag_NG(engaged_urls,ng_domains)
    engaged_handles_tagged = tag_NG_handles(engaged_handles,ng_domains)
    
    new_users = []
    new_domains = []
    new_tweet_ids = []
    new_age = []

    db_payload = []
    for i in range(len(users)):
        payload_dict = {
            'twitter_id':tweet_id_urls[i],
            'domain':urls_domain[i],
            'NG_rating':urls_rating[i],
            'NG_score':urls_score[i]
        }
        db_payload.append(payload_dict)
    finalJSON = []
    finalJSON.append(screen)
    finalJSON.append(db_payload)
    requests.post('http://127.0.0.1:5052/insert_tweet_NG_domains',json=finalJSON)
    
    for i in range(len(users)):
        if engaged_urls_tagged[i] != 'NA':
            new_users.append(users[i])
            new_domains.append(engaged_urls_tagged[i])
            new_tweet_ids.append(tweet_id_urls[i])
            new_age.append(age_urls[i])

    for i in range(len(users_handles)):
        if engaged_handles_tagged[i] != 'NA':
            new_users.append(users_handles[i])
            new_domains.append(engaged_handles_tagged[i])
            new_tweet_ids.append(tweet_id_handles[i])
            new_age.append(age_handles[i])
    
    pd_new_users = pd.concat([pd.DataFrame(new_users,columns=['Users']),
                              pd.DataFrame(new_domains,columns=['Items']),
                              pd.DataFrame(new_tweet_ids,columns=['TweetID']),
                              pd.DataFrame(new_age,columns=['Age'])],axis=1)

    #if screen == 2:
    #    pd_new_users = pd_new_users.groupby('Items').apply(lambda x: x.sort_values('Age')).reset_index(drop=True)
    #    pd_new_users = pd_new_users.groupby('Items').head(5).reset_index(drop=True)

    pd_new_users['rating_age'] = np.exp(-1.0*pd_new_users['Age']/pd_new_users['Age'].mean())
    
    return pd_new_users

def filter_tweets(feedtweets):
    level_1_tweets = []
    level_2_retweeted = []
    filtered_feedtweets = []
    for tweet in feedtweets:
        unique = False
        no_reply = True
        if tweet["id_str"] not in level_1_tweets:
            if "retweeted_status" in tweet.keys():
                if tweet["retweeted_status"]["id_str"] not in level_1_tweets and tweet["retweeted_status"]["id_str"] not in level_2_retweeted:
                    level_1_tweets.append(tweet["id_str"])
                    level_2_retweeted.append(tweet["retweeted_status"]["id_str"])
                    unique = True
            else:
                level_1_tweets.append(tweet["id_str"])
                unique = True
        if tweet["in_reply_to_status_id_str"]:
            no_reply = False
        if unique and no_reply:
            filtered_feedtweets.append(tweet)
    return filtered_feedtweets

def break_timeline_attention(public_tweets,public_tweets_score,absent_tweets,max_pages):
    db_tweet_payload = []
    db_tweet_attn_payload = []
    absent_tweets_ids = []
    rankk = 0
    tweetids_by_page = defaultdict(list)
    for (i,tweet) in enumerate(public_tweets):
        if type(tweet) == float:
                continue
        page = int(rankk/10)
        rank_in_page = (rankk%10) + 1
        db_tweet = {
            'fav_before':str(tweet['favorited']),
            'tid':str(tweet["id"]),
            'rtbefore':str(tweet['retweeted']),
            'page':page,
            'rank':rank_in_page,
            'predicted_score':public_tweets_score[i]
        }
        db_tweet_payload.append(db_tweet)
        tweetids_by_page[page].append(tweet["id"])
        rankk = rankk + 1

    for tweet in absent_tweets:
        if type(tweet) == float:
                continue
        absent_tweets_ids.append(tweet["id_str"])

    for attn_page in range(max_pages):
        present_tweets_ids = tweetids_by_page[attn_page]
        present_tweets_select = np.random.choice(present_tweets_ids,size=3,replace=False)
        absent_tweets_select = np.random.choice(absent_tweets_ids,size=2,replace=False)
        for absent_tweet_id in absent_tweets_select:
            absent_tweets_ids.remove(absent_tweet_id)
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
    return db_tweet_payload,db_tweet_attn_payload

def pageArrangementendless(ng_tweets, ng_tweets_ratings, non_ng_tweets):
    ranked_ng_tweets = []
    final_resultant_feed = []
    final_resultant_feed_score = []
    final_feed_length = len(ng_tweets) + len(non_ng_tweets)
    resultant_feed = [None] * final_feed_length
    resultant_score = [0.0] * final_feed_length

    #Rank the NG tweets
    for i in range(len(ng_tweets)):
        ranked_ng_tweets.append((ng_tweets[i], ng_tweets_ratings[i]))
    
    #Top 50 tweets from NewsGuard
    ranked_ng_tweets.sort(key=lambda a: a[1], reverse=True)
    top_50 = ranked_ng_tweets

    #50 other tweets
    other_tweets = non_ng_tweets

    pt = 0.5

    #Assign positions in feed to the NG and non NG tweets
    for i in range(len(resultant_feed)):
        if len(top_50) == 0:
            break
        if len(other_tweets) == 0:
            break
        chance = random.randint(1, 100)
        if chance < (pt * 100):
            resultant_feed[i] = top_50[0][0]
            resultant_score[i] = top_50[0][1]
            top_50.pop(0)
        else:
            resultant_feed[i] = other_tweets[0]
            resultant_score[i] = -100
            other_tweets.pop(0)
    
    if len(top_50) == 0:
        resultant_feed.extend(other_tweets)
        resultant_score.extend([-100]*(len(other_tweets)))
    if len(other_tweets) == 0:
        for tt in top_50:
            resultant_feed.append(tt[0])
            resultant_score.append(tt[1])

    for i in range(len(resultant_feed)):
        if resultant_feed[i] != None:
            final_resultant_feed.append(resultant_feed[i])
            final_resultant_feed_score.append(resultant_score[i])

    #print("Res Feed Len: " + str(len(final_resultant_feed)))
    return final_resultant_feed,final_resultant_feed_score

def main(proj_dir,data_dir,log_path=LOG_PATH_DEFAULT):
    logger = make_logger(log_path)
    logger.info(f"Training Cron job started: {proj_dir=} {data_dir=}")

    ng_fn = proj_dir + 'recsys/NewsGuardIffy/NG_2024_March.csv'
    iffyfile = proj_dir + 'recsys/NewsGuardIffy/iffy.csv'
    ng_domains = integrate_NG_iffy(ng_fn,iffyfile)
    print("Read NewsGuard")    
    """
    print("Training Job Starting")
    try:
        hoaxy_URLS = pd.read_csv('/home/rockwell/hoaxy_data_all/hoaxy_dataset_URLS_tagged.csv')
        hoaxy_URLS = hoaxy_URLS.drop(columns=['Unnamed: 0'])
        hoaxy_URLS = hoaxy_URLS.drop(columns=['index'])
        hoaxy_URLS.columns = ['Users','Items']
        hoaxy_handles = pd.read_csv('/home/rockwell/hoaxy_data_all/hoaxy_handles_screennames.csv')
        hoaxy_handles = hoaxy_handles.drop(columns=['Unnamed: 0'])
        hoaxy_handles = hoaxy_handles.dropna()
        hoaxy_handles.columns = ['Users','Items']
        pilot1_pilot2_URLS = pd.read_csv('/home/rockwell/hoaxy_data_all/pilot1_pilot2_URLS.csv')
        pilot1_pilot2_URLS = pilot1_pilot2_URLS.drop(columns=['Unnamed: 0','TweetID','Age'])
        pilot1_pilot2_authors = pd.read_csv('/home/rockwell/hoaxy_data_all/pilot1_pilot2_URLS.csv')
        pilot1_pilot2_authors = pilot1_pilot2_authors.drop(columns=['Unnamed: 0'])
        pd_training = pd.concat([hoaxy_URLS,hoaxy_handles,pilot1_pilot2_URLS,pilot1_pilot2_authors],ignore_index=True)
        print("Built Training Data")

        new_user_timeline_files = []
        new_fav_timeline_files = []

        for root, dirs, files in os.walk(os.path.abspath(data_dir+"usertimeline_data/")):
            for file in files:
                new_user_timeline_files.append(os.path.join(root, file))

        for root, dirs, files in os.walk(os.path.abspath(data_dir+"favorites_data/")):
            for file in files:
                new_fav_timeline_files.append(os.path.join(root, file))

        pd_new_users = get_data_from_new_users(new_user_timeline_files, new_fav_timeline_files, ng_domains)
        pd_new_users = pd_new_users.reset_index(drop=True)
        recsys_engagement = pd.concat([pd_training,pd_new_users],ignore_index=True)
        
        print("Appended pilot 3 users to training data")

        tot_users = len(recsys_engagement['Users'].unique())
        domain_idf = recsys_engagement.groupby('Items').Users.agg(idf,tot_users=tot_users)
        domain_idf_dict = {}
        for kk in domain_idf.keys():
            domain_idf_dict[kk] = domain_idf[kk]

        domain_rating_json_column = recsys_engagement.groupby('Users').Items.agg(tfidf,idf_dict=domain_idf_dict)
        
        print("Built TF-IDF")

        users_training = []
        domains_training = []
        ratings_training = []

        #Full training set
        for (i,uu) in enumerate(domain_rating_json_column.keys()):
            if i % 10000 == 0:
                print(i)
            rating_json = json.loads(domain_rating_json_column[uu])
            for dd in rating_json.keys():
                users_training.append(uu)
                domains_training.append(dd)
                ratings_training.append(rating_json[dd])

        pd_training = pd.concat([pd.DataFrame(users_training),pd.DataFrame(domains_training),pd.DataFrame(ratings_training)],axis=1)
        pd_training.columns = ['Users','Domains','Ratings']

        pd_training.to_csv(proj_dir + '/recsys/data/hoaxy_dataset_training_tfidf.csv')

        with open(proj_dir + '/recsys/data/domain_idf.json','w') as fp:
            json.dump(domain_idf_dict,fp)

        reader = surprise.reader.Reader(rating_scale=(0, 1))
        data = surprise.dataset.Dataset.load_from_df(pd_training, reader)

        algo = surprise.NMF(n_epochs=500,verbose=True)
        trainset = data.build_full_trainset()
        algo.fit(trainset)

        model_filename = proj_dir + '/recsys/model/hoaxy_recsys_model_tfidf.sav'
        joblib.dump(algo,model_filename)

        logger.info(f"Training Cron job fininshed: {proj_dir=}")

    except Exception as e:
        logger.error("Error in Training", exc_info=e)
    """
    print("Prediction Job Starting")
    logger.info("Prediction Cron job started")

    try:
        logger.info("Reading list of training domains")
        training_ng_domains_file = proj_dir + '/recsys/data/domain_idf.json'
        with open(training_ng_domains_file) as fn:
            domain_idf_dict = json.load(fn)
        training_ng_domains = domain_idf_dict.keys()

        logger.info("Preparing Training set")
        hoaxy_training_file = proj_dir + '/recsys/data/hoaxy_dataset_training_tfidf.csv'
        pd_hoaxy_training_dataset = pd.read_csv(hoaxy_training_file)
        pd_hoaxy_training_dataset = pd_hoaxy_training_dataset.drop(columns=['Unnamed: 0'])
        reader = surprise.reader.Reader(rating_scale=(0, 1))
        training_data = surprise.dataset.Dataset.load_from_df(pd_hoaxy_training_dataset, reader) 
        trainset = training_data.build_full_trainset()

        logger.info("Preparing model")
        model_file = proj_dir + '/recsys/model/hoaxy_recsys_model_tfidf.sav'
        algo = joblib.load(model_file)

        logger.info("Getting all new users")
        db_response = requests.get('http://127.0.0.1:5052/get_existing_training_user')
        user_ids = []
        screennames = []
        twitter_ids = []
        creation_dates = []
        if db_response.json()['data'] != "NEW":
            user_ids = [response[0] for response in db_response.json()['data']]
            screennames = [response[1] for response in db_response.json()['data']]
            twitter_ids = [response[2] for response in db_response.json()['data']]
            creation_dates = [response[3] for response in db_response.json()['data']]

        logger.info("Cheking eligibility according to account creation date")
        user_ids_eligible = []
        screennames_eligible = []
        twitter_ids_eligible = []
        for i in range(len(creation_dates)):
            user_id_itr = user_ids[i]
            creation_date_json = json.loads(creation_dates[i])
            print(creation_date_json)
            if "data" in creation_date_json.keys():
                if "created_at" in creation_date_json["data"][0].keys():
                    creation_date_arr = creation_date_json["data"][0]["created_at"].split('T')[0].split('-')
                    creation_date_datetime = datetime.datetime(int(creation_date_arr[0]),int(creation_date_arr[1]),int(creation_date_arr[2]))
                    if creation_date_datetime > datetime_eligibility:
                        logger.info(f"User not eligible creation date more {user_id_itr}")
                        requests.get('http://127.0.0.1:5052/set_user_eligibility?worker_id='+str(user_id_itr)+"&eligible=NO&non_eligibility_reason=Account creation date greater than December 1, 2023")
                    else:
                        user_ids_eligible.append(user_id_itr)
                        screennames_eligible.append(screennames[i])
                        twitter_ids_eligible.append(twitter_ids[i])
                else:
                    logger.info(f"User not eligible creation date doesn't exist {user_id_itr}")
                    requests.get('http://127.0.0.1:5052/set_user_eligibility?worker_id='+str(user_id_itr)+"&eligible=NO&non_eligibility_reason=Account creation date doesn't exist")
            else:
                logger.info(f"User not eligible creation date doesn't exist {user_id_itr}")
                requests.get('http://127.0.0.1:5052/set_user_eligibility?worker_id='+str(user_id_itr)+"&eligible=NO&non_eligibility_reason=Account creation date doesn't exist")

        logger.info("Getting screen 1 tweets")
        user_ids_eligible_2 = []
        screennames_eligible_2 = []
        twitter_ids_eligible_2 = []
        tweets_home = []
        for i in range(len(user_ids_eligible)):
            user_id_itr = user_ids_eligible[i]
            db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_all?worker_id='+str(user_ids_eligible[i]))
            db_response = db_response.json()['data']
            if db_response == "NEW":
                logger.info(f"User not eligible no home timeline {user_id_itr}")
                requests.get('http://127.0.0.1:5052/set_user_eligibility?worker_id='+str(user_id_itr)+"&eligible=NO&non_eligibility_reason=No data in home timeline")
            else:
                original_tweets_home = [response[7] for response in db_response]
                tweets_home.append(filter_tweets(original_tweets_home))
                user_ids_eligible_2.append(user_id_itr)
                screennames_eligible_2.append(screennames_eligible[i])
                twitter_ids_eligible_2.append(twitter_ids_eligible[i])
                #tweets_home.append([response[7] for response in db_response])
        
        logger.info("Getting screen 2 tweets")
        db_response_screen_2 = requests.get('http://127.0.0.1:5052/get_tweets_screen_2')
        feed_tweets_screen_2 = []
        if db_response_screen_2.json()['data'] != "NEW":
            original_feed_tweets_screen_2 = [response[1] for response in db_response_screen_2.json()['data']]
            feed_tweets_screen_2 = filter_tweets(original_feed_tweets_screen_2)
        else:
            logger.info("Prediction Cron job NO DATA SCREEN 2")
        pd_feed_tweets_screen_2 = get_data_from_hometimeline(feed_tweets_screen_2,"SAMPLE",ng_domains,2)
        pd_feed_tweets_screen_2 = pd_feed_tweets_screen_2.astype({'TweetID': 'int64'})

        for i in range(len(user_ids_eligible_2)):
            user_id_itr = user_ids_eligible_2[i]
            screen_name = screennames_eligible_2[i]
            try:
                inner_uid = trainset.to_inner_uid(screen_name)
            except:
                logger.info(f"User not eligible not present in the trainset {user_id_itr}")
                requests.get('http://127.0.0.1:5052/set_user_eligibility?worker_id='+str(user_id_itr)+"&eligible=NO&non_eligibility_reason=Not present in the training set")
                continue
            try:
                logger.info(f"Prediction Cron job Processing screen 1 {screen_name} {user_id_itr}")
                feed_tweets = tweets_home[i]
                worker_id = user_id_itr
                absent_tweets = feed_tweets[-10:]
                pd_feed_tweets = get_data_from_hometimeline(feed_tweets,screen_name,ng_domains,1)
                pd_feed_tweets = pd_feed_tweets.astype({'TweetID': 'int64'})
                predicted_rating = {}
                for index,row in pd_feed_tweets.iterrows():
                    if row['Items'] in training_ng_domains:
                        recsys_rating = algo.predict(uid=screen_name, iid=row['Items']).est
                        predicted_rating[row['TweetID']] = alpha_m*recsys_rating + alpha_t*row['rating_age']
                    else:
                        domain_not_present = row['Items']
                        #logger.info(f"NG domain not present in training screen 1 : {domain_not_present}")
                predicted_rating_tweets = predicted_rating.keys()
                NG_tweets = []
                NG_tweets_ratings = []
                non_NG_tweets = []
                for tweet in feed_tweets:
                    tweet_id = tweet['id']
                    if int(tweet_id) in predicted_rating_tweets:
                        NG_tweets.append(tweet)
                        NG_tweets_ratings.append(predicted_rating[int(tweet_id)])
                    else:
                        non_NG_tweets.append(tweet)
                feed_tweets_control,feed_tweets_control_score = pageArrangementendless(NG_tweets,NG_tweets_ratings,non_NG_tweets)
                max_pages = min([len(feed_tweets),5])
                db_tweet_control_payload,db_tweet_control_attn_payload = break_timeline_attention(feed_tweets_control,feed_tweets_control_score,absent_tweets,max_pages)
                finalJson = []
                finalJson.append(db_tweet_control_payload)
                finalJson.append(db_tweet_control_attn_payload)
                finalJson.append(worker_id)
                finalJson.append(screen_name)
                requests.post('http://127.0.0.1:5052/insert_timelines_attention_control',json=finalJson)

                logger.info(f"Prediction Cron job Processing screen 1 diversity {screen_name} {user_id_itr}")
                diversity_metrics = pd.read_csv(diversity_file)
                diversity_metrics = diversity_metrics.loc[diversity_metrics['n_visitors'] >= 10]
                domains_diversity = diversity_metrics['private_domain'].unique().tolist()
                predicted_rating_diversity = {}
                for index,row in pd_feed_tweets.iterrows():
                    if row['TweetID'] in predicted_rating.keys():
                        if row['Items'] in domains_diversity:
                            diversity_value_domain = diversity_metrics.loc[diversity_metrics['private_domain'] == row['Items']]['visitor_var'].values[0]
                            diversity_rating_domain = 1.0/(1.0 + math.exp(-1.0*(diversity_value_domain - 4.99)/1.0))
                        else:
                            diversity_rating_domain = -1
                        CF_val_std = (predicted_rating[row['TweetID']] - CF_STD_MEAN)/CF_STD_SD
                        D_val_std = (diversity_rating_domain - D_STD_MEAN)/D_STD_SD
                        predicted_rating_diversity[row['TweetID']] = 0.74*CF_val_std + 0.26*D_val_std
                        #else:
                        #    domain_not_present = row['Items']
                        #    logger.info(f"NG domain present in training but does not have diversity rating screen 1 : {domain_not_present}")
                        #    predicted_rating_diversity[row['TweetID']] = predicted_rating[row['TweetID']]
                        #    CF_val_std = (predicted_rating[row['TweetID']] - CF_STD_MEAN)/CF_STD_SD
                        #    predicted_rating_diversity[row['TweetID']] = 0.74*CF_val_std
                predicted_rating_tweets_diversity = predicted_rating_diversity.keys()
                NG_tweets_diversity = []
                NG_tweets_ratings_diversity = []
                non_NG_tweets_diversity = []
                for tweet in feed_tweets:
                    tweet_id = tweet['id']
                    if int(tweet_id) in predicted_rating_tweets_diversity:
                        NG_tweets_diversity.append(tweet)
                        NG_tweets_ratings_diversity.append(predicted_rating_diversity[int(tweet_id)])
                    else:
                        non_NG_tweets_diversity.append(tweet)
                feed_tweets_treatment,feed_tweets_treatment_score = pageArrangementendless(NG_tweets_diversity,NG_tweets_ratings_diversity,non_NG_tweets_diversity)
                max_pages = min([len(feed_tweets),5])
                db_tweet_treatment_payload,db_tweet_treatment_attn_payload = break_timeline_attention(feed_tweets_treatment,feed_tweets_treatment_score,absent_tweets,max_pages)
                finalJson = []
                finalJson.append(db_tweet_treatment_payload)
                finalJson.append(db_tweet_treatment_attn_payload)
                finalJson.append(worker_id)
                finalJson.append(screen_name)
                requests.post('http://127.0.0.1:5052/insert_timelines_attention_treatment',json=finalJson)

                logger.info(f"Prediction Cron job Processing screen 2 {screen_name} {user_id_itr}")
                absent_tweets_screen_2 = feed_tweets_screen_2[-10:]
                predicted_rating_screen_2 = {}
                for index,row in pd_feed_tweets_screen_2.iterrows():
                    if row['Items'] in training_ng_domains:
                        recsys_rating = algo.predict(uid=screen_name, iid=row['Items']).est
                        predicted_rating_screen_2[row['TweetID']] = alpha_m*recsys_rating + alpha_t*row['rating_age']
                    else:
                        domain_not_present = row['Items']
                        #logger.info(f"NG domain not present in training screen 2 : {domain_not_present}")
                predicted_rating_tweets_screen_2 = predicted_rating_screen_2.keys()
                NG_tweets_screen_2 = []
                NG_tweets_ratings_screen_2 = []
                non_NG_tweets_screen_2 = []
                for tweet in feed_tweets_screen_2:
                    tweet_id = tweet['id']
                    if int(tweet_id) in predicted_rating_tweets_screen_2:
                        NG_tweets_screen_2.append(tweet)
                        NG_tweets_ratings_screen_2.append(predicted_rating_screen_2[int(tweet_id)])
                    else:
                        non_NG_tweets_screen_2.append(tweet)
                feed_tweets_control_screen_2,feed_tweets_control_score_screen_2 = pageArrangementendless(NG_tweets_screen_2,NG_tweets_ratings_screen_2,non_NG_tweets_screen_2)
                max_pages = min([len(feed_tweets_control_screen_2),5])
                db_tweet_control_payload,db_tweet_control_attn_payload = break_timeline_attention(feed_tweets_control_screen_2,feed_tweets_control_score_screen_2,absent_tweets_screen_2,max_pages)
                finalJson = []
                finalJson.append(db_tweet_control_payload)
                finalJson.append(worker_id)
                finalJson.append(screen_name)
                requests.post('http://127.0.0.1:5052/insert_timelines_screen_2',json=finalJson)

                logger.info(f"Prediction Cron job Processing screen 2 diversity {screen_name} {user_id_itr}")
                absent_tweets_screen_2 = feed_tweets_screen_2[-10:]
                predicted_rating_screen_2_diversity = {}
                for index,row in pd_feed_tweets_screen_2.iterrows():
                    if row['TweetID'] in predicted_rating_screen_2.keys():
                        if row['Items'] in domains_diversity:
                            diversity_value_domain = diversity_metrics.loc[diversity_metrics['private_domain'] == row['Items']]['visitor_var'].values[0]
                            diversity_rating_domain = 1.0/(1.0 + math.exp(-1.0*(diversity_value_domain - 4.99)/1.0))
                        else:
                            diversity_rating_domain = -1
                        CF_val_std = (predicted_rating_screen_2[row['TweetID']] - CF_STD_MEAN)/CF_STD_SD
                        D_val_std = (diversity_rating_domain - D_STD_MEAN)/D_STD_SD
                        predicted_rating_screen_2_diversity[row['TweetID']] = 0.74*CF_val_std + 0.26*D_val_std
                        #else:
                        #    domain_not_present = row['Items']
                        #    logger.info(f"NG domain present in training but does not have diversity rating screen 2 : {domain_not_present}")
                        #    predicted_rating_screen_2_diversity[row['TweetID']] = predicted_rating_screen_2[row['TweetID']]
                        #    CF_val_std = (predicted_rating_screen_2[row['TweetID']] - CF_STD_MEAN)/CF_STD_SD
                        #    predicted_rating_screen_2_diversity[row['TweetID']] = 0.74*CF_val_std
                predicted_rating_tweets_screen_2_diversity = predicted_rating_screen_2_diversity.keys()
                NG_tweets_screen_2_diversity = []
                NG_tweets_ratings_screen_2_diversity = []
                non_NG_tweets_screen_2_diversity = []
                for tweet in feed_tweets_screen_2:
                    tweet_id = tweet['id']
                    if int(tweet_id) in predicted_rating_tweets_screen_2_diversity:
                        NG_tweets_screen_2_diversity.append(tweet)
                        NG_tweets_ratings_screen_2_diversity.append(predicted_rating_screen_2_diversity[int(tweet_id)])
                    else:
                        non_NG_tweets_screen_2_diversity.append(tweet) 
                feed_tweets_treatment_screen_2,feed_tweets_treatment_score_screen_2 = pageArrangementendless(NG_tweets_screen_2_diversity,NG_tweets_ratings_screen_2_diversity,non_NG_tweets_screen_2_diversity)                
                max_pages = min([len(feed_tweets_control_screen_2),5])
                db_tweet_treatment_payload,db_tweet_treatment_attn_payload = break_timeline_attention(feed_tweets_treatment_screen_2,feed_tweets_treatment_score_screen_2,absent_tweets_screen_2,max_pages)
                finalJson = []
                finalJson.append(db_tweet_treatment_payload)
                finalJson.append(worker_id)
                finalJson.append(screen_name)
                requests.post('http://127.0.0.1:5052/insert_timelines_screen_2_treatment',json=finalJson)

                #User is eligible. Set eligibility
                requests.get('http://127.0.0.1:5052/set_user_eligibility?worker_id='+str(user_id_itr)+"&eligible=YES&non_eligibility_reason=NA")

            except Exception as e:
                requests.get('http://127.0.0.1:5052/set_user_eligibility?worker_id='+str(user_id_itr)+"&eligible=NO&non_eligibility_reason=Prediction Failed due to some error")
                logger.error(f"Prediction Cron job Failed for {screen_name}",exc_info=e)
                continue

            logger.info(f"Prediction Cron job Finished for {screen_name} {user_id_itr}")

    except Exception as e:
        logger.error("Error in Prediction", exc_info=e)
    

if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    main(args.proj_dir,args.data_dir)

