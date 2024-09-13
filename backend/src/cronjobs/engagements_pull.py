import pytz
import json
import requests
import logging
import glob
import os
import gzip
import time
from datetime import datetime
from configparser import ConfigParser
from requests_oauthlib import OAuth1Session
from argparse import ArgumentParser

LOG_FMT_DEFAULT='%(asctime)s:%(levelname)s:%(message)s'
LOG_PATH_DEFAULT="/home/rockwell/Rockwell/backend/src/cronjobs/engagement_cronjob.log"

TWITTER_SEARCH_API_URL = "https://api.twitter.com/2/tweets/search/recent"

timeline_params_engagement = {
    "tweet.fields" : "id,text,edit_history_tweet_ids,attachments,author_id,conversation_id,created_at,entities,in_reply_to_user_id,lang,public_metrics,referenced_tweets,reply_settings",
    "user.fields" : "id,name,username,created_at,description,entities,location,pinned_tweet_id,profile_image_url,protected,public_metrics,url,verified",
    "media.fields": "media_key,type,url,duration_ms,height,preview_image_url,public_metrics,width",
    "expansions" : "author_id,referenced_tweets.id,attachments.media_keys",
    "max_results" : 10
}

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
    parser.add_argument("data_dir", help="directory with data files")
    parser.add_argument("collection_count", help="How many tweets to collect")
    parser.add_argument("collection_days", help="How many days to continue collecting tweets")
    parser.add_argument("stop_date", help="What is the stop date in UTC timezone")
    return parser

def main(data_dir, collection_count, collection_days, stop_time, log_path=LOG_PATH_DEFAULT):
    logger = make_logger(log_path)
    logger.info(f"Engagement Pulling program started: {data_dir=}, {collection_count=}, {stop_time=}")
    try:
        dateformat = "%Y-%m-%dT%H:%M:%S"
        stop_time_datetime = datetime.strptime(stop_time, dateformat)
        stop_time_datetime_utc = stop_time_datetime.astimezone(pytz.utc)
    except Exception as e:
        logger.error(f"Problem in processing stop time", exc_info=e)
        return
    try:
        cred = config('../configuration/config.ini','twitterapp')
    except Exception as e:
        logger.error(f"Problem getting Twitter keys from Configuration", exc_info=e)
        return
    data_dir = os.path.abspath(data_dir)
    curr_dir = os.getcwd()
    try:
        os.chdir(data_dir)
        while True:
            time_now_local = datetime.now()
            time_now = datetime.now(pytz.utc)
            if time_now > stop_time_datetime_utc:
                break
            engagement_files = sorted(glob.glob("*_eng.json.gz"))
            for eng_file in engagement_files:
                path = os.path.join(data_dir, eng_file)
                logger.info(f"Engagement pull for file: {eng_file=}")
                with gzip.open(path, 'r') as fin:
                    try:
                        user_dict = json.loads(fin.read().decode('utf-8'))
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON data: {path}", exc_info=e)
                        continue
                    except UnicodeError as e:
                        logger.error(f"Error decoding UTF-8 data: {path}", exc_info=e)
                        continue
                    except IOError as e:
                        logger.error(f"I/O error reading data: {path} ", exc_info=e)
                        continue
                try:
                    access_token = user_dict['accessToken']
                    access_token_secret = user_dict['accessTokenSecret']
                    collection_started_date = user_dict['collectionStarted']
                    user_object = user_dict['userObject']
                    screenname = user_dict['userObject']['screen_name']
                    mturk_id = user_dict['MTurkId']
                    mturk_hit_id = user_dict['MTurkHitId']
                    mturk_assignment_id = user_dict['MTurkAssignmentId']
                    worker_id = user_dict["worker_id"]
                    tweets_collected = user_dict['tweets_collected']
                    eng_tweets = user_dict['engTweets'].copy()
                    user_queries = user_dict['user_queries'].copy()
                    idx_start = user_dict['idx_start']
                    print("Pulling data for file and screename: "+str(eng_file)+","+str(screenname))
                except KeyError as e:
                    logger.error(f"Problem getting fields for file {eng_file=}", exc_info=e)
                    continue
                if tweets_collected > int(collection_count):
                    logger.info(f"Engagement pull stopped for file because required number of tweets_collected: {eng_file=} {tweets_collected=}")
                    continue
                collection_started_datetime = datetime.strptime(collection_started_date, dateformat)
                difference_dates = time_now_local - collection_started_datetime
                difference_dates_days = difference_dates.days
                if difference_dates_days > 7:
                    logger.info(f"Engagement pull stopped for file because one week over: {eng_file=}")
                    continue
                oauth = OAuth1Session(cred['key'],
                    client_secret=cred['key_secret'],
                    resource_owner_key=access_token,
                    resource_owner_secret=access_token_secret)
                logger.info(f"Processing file screenname start index: {eng_file=} {screenname=} {idx_start=}")
                ii_query = idx_start
                while True:
                    print("Processing query : "+str(ii_query))
                    user_query_new = {}
                    user_query_new['query'] = user_queries[ii_query]['query']
                    user_query_new['since_id'] = user_queries[ii_query]['since_id']
                    user_query_new['next_token'] = '##START##'
                    timeline_params_engagement['query'] = user_queries[ii_query]['query']
                    if user_queries[ii_query]['since_id'] != '0':
                        timeline_params_engagement['since_id'] = user_queries[ii_query]['since_id']
                    if user_queries[ii_query]['next_token'] != '##START##':
                        timeline_params_engagement['next_token'] = user_queries[ii_query]['next_token']
                    response = oauth.get(TWITTER_SEARCH_API_URL, params = timeline_params_engagement)
                    v2tweetobj = json.loads(response.text)
                    if 'status' in v2tweetobj.keys():
                        if v2tweetobj['status'] == 429:
                            print("Rate limit exceeded for file : "+str(eng_file)+" at index : "+str(ii_query))
                            logger.info(f"Rate limit exceeded for file index: {eng_file=} {ii_query=}")
                            break
                        elif v2tweetobj['status'] != 200:
                            print("Probably got some error for file : "+str(eng_file)+" at index : "+str(ii_query))
                            print(v2tweetobj)
                            logger.info(f"Probably got some error for file index: {eng_file=} {ii_query=}")
                            logger.info(f"Probably got some error return object: {v2tweetobj}")
                    if 'meta' in v2tweetobj.keys():
                        if 'result_count' in v2tweetobj['meta'].keys():
                            print("Number of tweets pulled : "+str(v2tweetobj['meta']['result_count']))
                            num_tweets = v2tweetobj['meta']['result_count']
                            tot_tweets = tweets_collected + v2tweetobj['meta']['result_count']
                            logger.info(f"Number of tweets pulled for file index: {eng_file=} {ii_query=} {num_tweets=} {tot_tweets=}")
                            if v2tweetobj['meta']['result_count'] > 0:
                                if 'data' in v2tweetobj.keys():
                                    eng_tweets.append(response.text)
                                    tweets_collected = tweets_collected + v2tweetobj['meta']['result_count']
                                    if 'next_token' in v2tweetobj['meta'].keys():
                                        user_query_new['next_token'] = v2tweetobj['meta']['next_token']
                                    else:
                                        user_query_new['since_id'] = v2tweetobj['meta']['newest_id']
                    user_queries[ii_query] = user_query_new
                    ii_query = ii_query + 1
                    if ii_query == len(user_queries):
                        ii_query = 0
                    if tweets_collected > int(collection_count):
                        logger.info(f"Engagement pull stopped for file because required number of tweets_collected: {eng_file=} {tweets_collected=}")
                        break
                logger.info(f"Writing new file for: {eng_file=}")
                writeObjeng = {
                    'accessToken' : access_token,
                    'accessTokenSecret' : access_token_secret,
                    'collectionStarted' : collection_started_date,
                    'userObject' : user_object,
                    'MTurkId' : mturk_id,
                    'MTurkHitId' : mturk_hit_id,
                    'MTurkAssignmentId' : mturk_assignment_id,
                    'worker_id' : worker_id,
                    'tweets_collected' : tweets_collected,
                    'engTweets' : eng_tweets,
                    'user_queries' : user_queries,
                    'idx_start' : ii_query 
                }
                with gzip.open(path,"w") as outfile:
                    outfile.write(json.dumps(writeObjeng).encode('utf-8'))
                logger.info(f"Wrote new file for: {eng_file=}")  
            print("Sleeping for 18 mins!!!")
            time.sleep(1080) #sleep for 18 minutes
        os.chdir(curr_dir)
        return
    except Exception as e:
        print(e)
    finally:
        os.chdir(curr_dir)
        return

def main_prev(data_dir, collection_count, log_path=LOG_PATH_DEFAULT):
    time_now = datetime.now()
    logger = make_logger(log_path)
    logger.info(f"Engagement pull cron job started: {data_dir=}, {collection_count=}")
    print("Engagement cronjob started")
    try:
        cred = config('../configuration/config.ini','twitterapp')
    except Exception as e:
        logger.error(f"Problem getting Twitter keys from Configuration", exc_info=e)
        print("Problem getting Twitter keys from Configuration")
        return
    data_dir = os.path.abspath(data_dir)
    curr_dir = os.getcwd()
    try:
        os.chdir(data_dir)
        engagement_files = sorted(glob.glob("*_eng.json.gz"))
        users = []
        for eng_file in engagement_files:
            path = os.path.join(data_dir, eng_file)
            logger.info(f"Engagement pull for file: {eng_file=}")
            with gzip.open(path, 'r') as fin:
                try:
                    data = json.loads(fin.read().decode('utf-8'))
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON data: {path}", exc_info=e)
                    continue
                except UnicodeError as e:
                    logger.error(f"Error decoding UTF-8 data: {path}", exc_info=e)
                    continue
                except IOError as e:
                    logger.error(f"I/O error reading data: {path} ", exc_info=e)
                    continue
            try:
                access_token = data['accessToken']
                access_token_secret = data['accessTokenSecret']
                user_object = data['userObject']
                screenname = data['userObject']['screen_name']
                mturk_id = data['MTurkId']
                mturk_hit_id = data['MTurkHitId']
                mturk_assignment_id = data['MTurkAssignmentId']
                worker_id = data["worker_id"]
                since_id = data['latestTweetId']
                tweets_collected = data['tweets_collected']
                eng_tweets = data['engTweets']
            except KeyError as e:
                logger.error(f"Problem getting fields for file {eng_file=}", exc_info=e)
                continue
            try:
                user_queries = compose_queries_512_chars(screenname)
                user_queries_tot = len(user_queries)
                print("Length of queries : ")
                print(user_queries_tot)
                next_tokens = ['##START##']*user_queries_tot
                user_dict = {}
                user_dict['access_token'] = access_token
                user_dict['access_token_secret'] = access_token_secret
                user_dict['user_object'] = user_object
                user_dict['screenname'] = screenname
                user_dict['mturk_id'] = mturk_id
                user_dict['mturk_hit_id'] = mturk_hit_id
                user_dict['mturk_assignment_id'] = mturk_assignment_id
                user_dict['worker_id'] = worker_id
                user_dict['since_id'] = since_id
                user_dict['tweets_collected'] = tweets_collected
                user_dict['user_queries'] = user_queries
                user_dict['next_tokens'] = next_tokens
                user_dict['lastpull_timestamp'] = None
                user_dict['idx_start'] = 0
                user_dict['eng_tweets'] = eng_tweets
                user_dict['eng_file_name'] = eng_file
                users.append(user_dict)
            except Exception as e:
                logger.error(f"Problem in making the user dictionary for file {eng_file=}", exc_info=e)
                continue
        users_done_switch = [1]*len(users)
        users_max_tweet = ['0']*len(users)
        debugdict = []
        while True:
            if sum(users_done_switch) == 0:
                break
            users_new = []
            for (idx_user,user_dict) in enumerate(users):
                if users_done_switch[idx_user] == 0:
                    continue
                user_dict_new = {}
                user_dict_new['access_token'] = user_dict['access_token']
                user_dict_new['access_token_secret'] = user_dict['access_token_secret']
                user_dict_new['user_object'] = user_dict['user_object']
                user_dict_new['screenname'] = user_dict['screenname']
                user_dict_new['mturk_id'] = user_dict['mturk_id']
                user_dict_new['mturk_hit_id'] = user_dict['mturk_hit_id']
                user_dict_new['mturk_assignment_id'] = user_dict['mturk_assignment_id']
                user_dict_new['worker_id'] = user_dict['worker_id']
                user_dict_new['user_queries'] = user_dict['user_queries']
                user_dict_new['eng_file_name'] = user_dict['eng_file_name']
                oauth = OAuth1Session(cred['key'],
                    client_secret=cred['key_secret'],
                    resource_owner_key=user_dict['access_token'],
                    resource_owner_secret=user_dict['access_token_secret'])
                if user_dict['tweets_collected'] >= int(collection_count):
                    users_done_switch[idx_user] = 0
                    users_new.append(user_dict)
                    continue
                if user_dict['lastpull_timestamp']:
                    mins_diff = (datetime.now() - user_dict['lastpull_timestamp']).total_seconds() / 60.0
                    if mins_diff < TWITTER_SEARCH_API_RATE_LIMIT_TIME:
                        users_new.append(user_dict)
                        continue
                user_dict_new['lastpull_timestamp'] = datetime.now()
                eng_tweets_continued = user_dict['eng_tweets'].copy()
                tweets_collected_itr = 0
                user_queries = user_dict['user_queries']
                next_tokens = user_dict['next_tokens'].copy()
                since_id = user_dict['since_id']
                ii_query = user_dict['idx_start']
                while ii_query < len(user_queries):
                    if next_tokens[ii_query] == '##DONE##':
                        continue
                    if user_dict['tweets_collected'] + tweets_collected_itr > int(collection_count):
                        users_done_switch[idx_user] = 0
                        break
                    timeline_params_engagement['query'] = user_queries[ii_query]
                    if user_dict['since_id'] != '0':
                        timeline_params_engagement['since_id'] = user_dict['since_id']
                    if next_tokens[ii_query] != '##START##':
                        timeline_params_engagement['next_token'] = next_tokens[ii_query]
                    response = oauth.get(TWITTER_SEARCH_API_URL, params = timeline_params_engagement)
                    v2tweetobj = json.loads(response.text)
                    debugdict.append({'query':user_queries[ii_query],'response':v2tweetobj})
                    print(ii_query)
                    print(user_queries[ii_query])
                    print(v2tweetobj)
                    if 'status' in v2tweetobj.keys():
                        if v2tweetobj['status'] == 429:
                            break
                    if 'meta' in v2tweetobj.keys():
                        if 'result_count' in v2tweetobj['meta'].keys():
                            if v2tweetobj['meta']['result_count'] > 0:
                                if 'data' in v2tweetobj.keys():
                                    eng_tweets_continued.append(response.text)
                                    tweets_collected_itr = tweets_collected_itr + v2tweetobj['meta']['result_count']
                                    if int(v2tweetobj['meta']['newest_id']) > int(since_id):
                                        since_id = v2tweetobj['meta']['newest_id']
                        if 'next_token' in v2tweetobj['meta'].keys():
                            next_tokens[ii_query] = v2tweetobj['meta']['next_token']
                        else:
                            next_tokens[ii_query] = '##DONE##'
                    ii_query = ii_query + 1
                    if ii_query == len(user_queries):
                        any_next_token = False
                        for nt in next_tokens:
                            if nt != '##DONE##':
                                any_next_token = True
                                break
                        if any_next_token:
                            ii_query = 0
                        else:
                            users_done_switch[idx_user] = 0
                user_dict_new['idx_start'] = ii_query
                user_dict_new['eng_tweets'] = eng_tweets_continued
                user_dict_new['next_tokens'] = next_tokens
                user_dict_new['since_id'] = since_id
                user_dict_new['tweets_collected'] = user_dict['tweets_collected'] + tweets_collected_itr
                users_new.append(user_dict_new)
            users = users_new
            print("Sleeping for 18 mins!!!!")
            time.sleep(1080) #sleep for 18 minutes 
        for user in users:
            writeObj = {
                "MTurkId" : user['mturk_id'],
                "MTurkHitId" : user['mturk_hit_id'],
                "MTurkAssignmentId" : user['mturk_assignment_id'],
                "accessToken" : user['access_token'],
                "accessTokenSecret" : user['access_token_secret'], 
                "worker_id" : user['worker_id'],
                "userObject" : user['user_object'],
                "latestTweetId" : user['since_id'],
                "tweets_collected" : user['tweets_collected'],
                "engTweets" : user['eng_tweets']
            }

            path = os.path.join(data_dir, user['eng_file_name'])

            with gzip.open(path,"w") as outfile:
                outfile.write(json.dumps(writeObj).encode('utf-8'))

        with gzip.open('/home/rockwell/Rockwell/backend/src/cronjobs/debugfile.json.gz',"w") as outfile:
            outfile.write(json.dumps(debugfile).encode('utf-8'))


    except Exception as e:
        print(e)
    finally:
        os.chdir(curr_dir)

if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    main(args.data_dir,args.collection_count,args.collection_days,args.stop_date)
