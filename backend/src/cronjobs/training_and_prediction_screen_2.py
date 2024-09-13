#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  3 00:51:18 2023

@author: saumya
"""

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
import surprise
import psycopg2
from collections import Counter
from collections import defaultdict
from configparser import ConfigParser
from multiprocessing import Manager
from multiprocessing.dummy import Pool
from argparse import ArgumentParser

LOG_FMT_DEFAULT='%(asctime)s:%(levelname)s:%(message)s'
LOG_PATH_DEFAULT="/home/rockwell/Rockwell/backend/src/cronjobs/prediction_cronjob.log"

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
    uk = u.encode('utf-8')
    if uk in _CACHE:
        return _CACHE[uk]
    try:
        r = requests.head(u, allow_redirects=True,timeout=10)
        _CACHE[uk] = r.url
        return r.url
    except requests.exceptions.RequestException:
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
    
    ng_domain_values = ng_domains['domain'].values
    
    for iffy_domain in iffy_domains:
        if iffy_domain not in ng_domain_values:
            df_iffy = {'domain':iffy_domain,'rank':'N','score':-100,'twitter':'NA'}
            ng_domains = ng_domains.append(df_iffy,ignore_index=True)

    return ng_domains

def unshorten_and_tag_NG(all_urls,ng_domains):
    ng_domain_values = ng_domains.loc[ng_domains['rank'].isin(['T','N'])]['domain'].unique()
    ng_twitter_values = ng_domains.loc[ng_domains['rank'].isin(['T','N'])]['twitter'].unique()
    urls_unshorted = []
    outputs = unshorten(all_urls, threads=20, cachepath='/home/saumya/')
    for url in outputs:
        urls_unshorted.append(url)
    
    urls_domains = []
    urls_twitter = []
    for url in urls_unshorted:
        domain = ".".join(url.split("/")[2].split(".")[-2:])
        urls_domains.append(domain)
        if domain == "twitter.com":
            try:
                urls_twitter.append(url.split("/")[3])
            except:
                urls_twitter.append("NA")
        else:
            urls_twitter.append("NA")
    
    urls_tagged = []
    for idx in range(len(urls_domains)):
        if urls_domains[idx] in ng_domain_values:
            urls_tagged.append(urls_domains[idx])
        elif urls_twitter[idx] != "NA":
            if urls_twitter[idx] in ng_twitter_values: 
                try:
                    twitter_domain = ng_domains.loc[(ng_domains['twitter'] == urls_twitter[idx])]['domain'][0]
                    urls_tagged.append(twitter_domain)
                except KeyError:
                    urls_tagged.append("NA")
                    continue
            else:
                urls_tagged.append("NA")
        else:
            urls_tagged.append("NA")
    return urls_tagged

def tag_NG_handles(all_handles,ng_domains):
    ng_twitter_values = ng_domains['twitter'].unique()
    handles_tagged = []
    for handle in all_handles:
        if handle in ng_twitter_values:
            corrs_domain = ng_domains.loc[(ng_domains['twitter'] == handle)]['domain'].values.tolist()
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

def get_data_from_new_users(user_timeline_files,fave_timeline_files,ng_domains,logger):

    users = []
    engaged_urls = []
    
    users_handles = []
    engaged_handles = []

    print("IN GET DATA!!!!")
    print(user_timeline_files)
    print(fave_timeline_files)

    #hoaxy_config = config('../configuration/config.ini','hoaxy_database')
    
    for fn in user_timeline_files:
        with gzip.open(fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            if data['userTweets']:
                user_id = data["userObject"]["screen_name"]
                user_twitter_id = data["userObject"]["twitter_id"]
                tweets_covered = []
                for tweet in data['userTweets']:
                    tweets_covered.append(tweet['id'])
                    if 'retweeted_status' in tweet:
                        users_handles.append(user_id)
                        engaged_handles.append(tweet['retweeted_status']['user']['screen_name'])
                        urls_extracted = extractfromentities(tweet['retweeted_status'])
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet['retweeted_status']:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['retweeted_status']['quoted_status']['user']['screen_name'])
                            urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                    else:
                        if 'quoted_status' in tweet:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['quoted_status']['user']['screen_name'])
                            urls_extracted = extractfromentities(tweet['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                        urls_extracted = extractfromentities(tweet)
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                """
                hoaxy_tweets,err_message = get_hoaxy_engagement(user_twitter_id,hoaxy_config)
                if err_message != "NA":
                    logger.info(f"Error in getting hoaxy tweets for {user_twitter_id=}")
                else:
                    for tweet in hoaxy_tweets:
                        if tweet['id'] in tweets_covered:
                            continue
                        if 'retweeted_status' in tweet:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['retweeted_status']['user']['screen_name'])
                            urls_extracted = extractfromentities(tweet['retweeted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                            if 'quoted_status' in tweet['retweeted_status']:
                                users_handles.append(user_id)
                                engaged_handles.append(tweet['retweeted_status']['quoted_status']['user']['screen_name'])
                                urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                                for url in urls_extracted:
                                    users.append(user_id)
                                    engaged_urls.append(url)
                        else:
                            if 'quoted_status' in tweet:
                                users_handles.append(user_id)
                                engaged_handles.append(tweet['quoted_status']['user']['screen_name'])
                                urls_extracted = extractfromentities(tweet['quoted_status'])
                                for url in urls_extracted:
                                    users.append(user_id)
                                    engaged_urls.append(url)
                            urls_extracted = extractfromentities(tweet)
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                """
                            
    for fn in fave_timeline_files:
        with gzip.open(fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            if data['likedTweets']:
                user_id = data["userObject"]["screen_name"]
                for tweet in data['likedTweets']:
                    if 'retweeted_status' in tweet:
                        users_handles.append(user_id)
                        engaged_handles.append(tweet['retweeted_status']['user']['screen_name'])
                        urls_extracted = extractfromentities(tweet['retweeted_status'])
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet['retweeted_status']:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['retweeted_status']['quoted_status']['user']['screen_name'])
                            urls_extracted = extractfromentities(tweet['retweeted_status']['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
                    else:
                        urls_extracted = extractfromentities(tweet)
                        for url in urls_extracted:
                            users.append(user_id)
                            engaged_urls.append(url)
                        if 'quoted_status' in tweet:
                            users_handles.append(user_id)
                            engaged_handles.append(tweet['quoted_status']['user']['screen_name'])
                            urls_extracted = extractfromentities(tweet['quoted_status'])
                            for url in urls_extracted:
                                users.append(user_id)
                                engaged_urls.append(url)
    
    print(len(engaged_urls))
    engaged_urls_tagged = unshorten_and_tag_NG(engaged_urls,ng_domains)
    engaged_handles_tagged = tag_NG_handles(engaged_handles,ng_domains)
    
    new_users_training = []
    new_domains_training = []
    
    for i in range(len(users)):
        if engaged_urls_tagged[i] != 'NA':
            new_users_training.append(users[i])
            new_domains_training.append(engaged_urls_tagged[i])

    for i in range(len(users_handles)):
        if engaged_handles_tagged[i] != 'NA':
            new_users_training.append(users_handles[i])
            new_domains_training.append(engaged_handles_tagged[i])
        else:
            new_users_training.append(users_handles[i])
            new_domains_training.append(engaged_handles[i])
    
    pd_new_users = pd.concat([pd.DataFrame(new_users_training,columns=['Users']),pd.DataFrame(new_domains_training,columns=['Items'])],axis=1)
    return pd_new_users

def get_handles_from_new_users(user_timeline_files,fave_timeline_files,ng_domains,logger):
    users_handle = []
    handles = []
    
    for fn in user_timeline_files:
        with gzip.open(fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            if data['userTweets']:
                for tweet in data['userTweets']:
                    if 'retweeted_status' in tweet:
                        users_handle.append(data["userObject"]["screen_name"])
                        handles.append(tweet['retweeted_status']['user']['screen_name'])
                            
    for fn in fave_timeline_files:
        with gzip.open(fn, 'r') as fin:
            data = json.loads(fin.read().decode('utf-8'))
            relevantkey = 'favTweets'
            if 'likedTweets' in data.keys():
                relevantkey = 'likedTweets'
            if data[relevantkey]:
                for tweet in data[relevantkey]:
                    if 'retweeted_status' in tweet:
                        users_handle.append(data["userObject"]["screen_name"])
                        handles.append(tweet['retweeted_status']['user']['screen_name'])
    
    handles_tagged = tag_NG_handles(handles, ng_domains)
    
    users_filtered = []
    handles_filtered = []
    
    for i in range(len(users_handle)):
        if handles_tagged[i] == 'NA':
            users_filtered.append(users_handle[i])
            handles_filtered.append(handles[i])
    
    pd_new_users_handles = pd.concat([pd.DataFrame(users_filtered),pd.DataFrame(handles_filtered)],axis=1)
    return pd_new_users_handles

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
    print(absent_tweets)
    all_tweet_ids = [tweet['id'] for tweet in public_tweets if type(tweet) != float]
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

def main(proj_dir,data_dir,log_path=LOG_PATH_DEFAULT):
    logger = make_logger(log_path)
    logger.info(f"Training Cron job started: {proj_dir=} {data_dir=}")
    print("Training Job Starting")
    """
    try:
        ng_fn = proj_dir + "/recsys/NewsGuardIffy/label-2022101916.json"
        iffyfile = proj_dir + "/recsys/NewsGuardIffy/iffy.csv"
        ng_domains = integrate_NG_iffy(ng_fn,iffyfile)
        print("Read NewsGuard")

        #recsys_engagement = pd.read_csv(proj_dir + '/recsys/data/hoaxy_dataset.csv')
        #if 'Unnamed: 0' in recsys_engagement.columns:
        #    recsys_engagement = recsys_engagement.drop(columns=['Unnamed: 0'])
        #recsys_engagement = recsys_engagement.reset_index(drop=True)
        
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
        print(pd_training.isnull().values.any())
        print("Built Training Data")

        new_user_timeline_files = []
        new_fav_timeline_files = []

        for root, dirs, files in os.walk(os.path.abspath(data_dir+"usertimeline_data/")):
            for file in files:
                new_user_timeline_files.append(os.path.join(root, file))

        for root, dirs, files in os.walk(os.path.abspath(data_dir+"favorites_data/")):
            for file in files:
                new_fav_timeline_files.append(os.path.join(root, file))

        pd_new_users = get_data_from_new_users(new_user_timeline_files, new_fav_timeline_files, ng_domains, logger)
        pd_new_users = pd_new_users.reset_index(drop=True)
        pd_new_users.columns = ['Users','Items']
        pd_new_users_authors = get_handles_from_new_users(new_user_timeline_files, new_fav_timeline_files, ng_domains, logger)
        pd_new_users_authors = pd_new_users_authors.reset_index(drop=True)
        pd_new_users_authors.columns = ['Users','Items']
        recsys_engagement = pd.concat([pd_training,pd_new_users,pd_new_users_authors],ignore_index=True)
        print(recsys_engagement.head())
        print(recsys_engagement.isnull().values.any())
        
        print("Appended pilot 3 users to training data")

        tot_users = len(recsys_engagement['Users'].unique())
        domain_idf = recsys_engagement.groupby('Items').Users.agg(idf,tot_users=tot_users)
        domain_idf_dict = {}
        for kk in domain_idf.keys():
            domain_idf_dict[kk] = domain_idf[kk]

        domain_rating_json_column = recsys_engagement.groupby('Users').Items.agg(tfidf,idf_dict=domain_idf_dict)
        
        print("Built TF-IDF")
        #domain_rating_json_column = recsys_engagement.groupby('user').NG_domain.agg(rating_calculate)

        #all_users = []
        #for uu in domain_rating_json_column.index:
        #    rating_json = json.loads(domain_rating_json_column[uu])
        #    if 'domain' not in rating_json.keys():
        #        all_users.append(uu)

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
        #pd_training_domains = pd.DataFrame(pd_training['Domains'].unique().tolist(),columns=['Domains'])

        pd_training.to_csv(proj_dir + '/recsys/data/hoaxy_dataset_training_tfidf.csv')
        #pd_training_domains.to_csv('../data/hoaxy_dataset_training_domains_2.csv')

        with open(proj_dir + '/recsys/data/domain_idf.json','w') as fp:
            json.dump(domain_idf_dict,fp)

        reader = surprise.reader.Reader(rating_scale=(0, 1))
        data = surprise.dataset.Dataset.load_from_df(pd_training, reader)

        algo = surprise.SVD()
        trainset = data.build_full_trainset()
        algo.fit(trainset)

        model_filename = proj_dir + '/recsys/model/hoaxy_recsys_model_tfidf.sav'
        joblib.dump(algo,model_filename)

        logger.info(f"Training Cron job fininshed: {proj_dir=}")

    except Exception as e:
        logger.error("Error in Training", exc_info=e)
    """
    logger.info("Prediction Cron job started")

    try:
        db_response = requests.get('http://127.0.0.1:5052/get_existing_tweets_all_screenname')
        screen_name_home = []
        if db_response.json()['data'] != "NEW":
            screen_name_home = [response[0] for response in db_response.json()['data']]
            worker_id_home = [response[1] for response in db_response.json()['data']]
        else:
            logger.info("Prediction Cron job NO DATA")
            return
        db_response = requests.get('http://127.0.0.1:5052/get_tweets_screen_2')
        feed_tweets = []
        if db_response.json()['data'] != "NEW":
            feed_tweets = [response[1] for response in db_response.json()['data']]
        pilot_3_screennames = ['AGamez1319', 'Ahorito_', 'Allisnwundrlnd4', 'BSPhD', 'DaveSaub',
               'Drama4DaMama', 'DustyBr45669109', 'KonaBradford', 'PhilMilz',
               'Random_Outlier', 'ThinkOG', 'Tombstonepicnic', 'bigrigbrod65964',
               'eckardrecords', 'focalexpress', 'itbwhatitb76', 'jamesli1pro',
               'jasmine_raynee', 'joonswear', 'julia_b_knight', 'killsongz',
               'kliewer_daniel', 'kraigsdecker', 'regtypeDEWD', 'tardigraded',
               'willmittenthal']
        all_screenname = list(set(screen_name_home))
        for screen_name in all_screenname:
            if screen_name not in pilot_3_screennames:
                continue
            try:
                logger.info(f"Prediction Cron job Processing {screen_name}")
                print(f"Prediction Cron job Processing {screen_name}")
                worker_id = [worker_id_home[i] for i in range(len(screen_name_home)) if screen_name_home[i] == screen_name][0]
                absent_tweets = feed_tweets[-10:]
                timeline_json = [feed_tweets,screen_name]
                recsys_response = requests.get('http://127.0.0.1:5053/recsys_rerank',json=timeline_json)
                if recsys_response.json()['data'] == "NOTPRESENT":
                    logger.info(f"Prediction Cron job screen_name not present {screen_name}")
                    print(f"Prediction Cron job screen_name not present {screen_name}")
                    continue    
                feed_tweets_control = recsys_response.json()['data'][0]
                feed_tweets_control_score = recsys_response.json()['data'][1]
                max_pages = min([len(feed_tweets),5])
                db_tweet_control_payload,db_tweet_control_attn_payload = break_timeline_attention(feed_tweets_control,feed_tweets_control_score,absent_tweets,max_pages)
                finalJson = []
                finalJson.append(db_tweet_control_payload)
                finalJson.append(worker_id)
                finalJson.append(screen_name)
                requests.post('http://127.0.0.1:5052/insert_timelines_screen_2',json=finalJson)
            except Exception as e:
                logger.error(f"Prediction Cron job Failed for {screen_name}",exc_info=e)
                continue

            logger.info(f"Prediction Cron job Finished for {screen_name}")

    except Exception as e:
        logger.error("Error in Prediction", exc_info=e)

if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    main(args.proj_dir,args.data_dir)