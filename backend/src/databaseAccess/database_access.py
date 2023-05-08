from flask import Flask, render_template, request, url_for, jsonify
import json
import random, string
from database_config import config
import psycopg2
from psycopg2 import pool
import datetime
import time
import asyncio

#Global pool variable:
pool_is_full = False
MIN = 5
MAX = 100
universal_buffer = []
params = config('../configuration/config.ini','postgresql_local')
accessPool =  psycopg2.pool.SimpleConnectionPool(MIN, MAX,host=params["host"],database=params["database"],user=params["user"],password=params["password"],port=params["port"])# Maybe make 2 pools and half the functions use each or make this one huge.
print("Access Pool object")
print(accessPool)
app = Flask(__name__)

app.debug = False

worker_id_store = {}

# Is full Universal to check when function calls, if is full is true our buffer is being used (push package immediately), if not continue as normal
# WINNER:::I should make it normal where we can call them all but on overflow it is pushed to queue here and then the loop function is called, now on empty terminate. (if it keeps being added to it keeps going)
#def queueLoop() -> None: # async so it doesnt interfere with the rest of the execution.
#            """ Hold a queue of overflow and squeeze them in as the program runs """
#            # Main loop of the dequeue function
#            while True: # Runs throughout program to flush queue.
#                while len(universal_buffer) > 0:
#                    try:
#                        info = universal_buffer.pop(0) # Get the first in line (put in function call) Deleteing with pop, if write fails it will be added here again through the function itself.
#                        if info.at(0) == "insert_tweet":
#                            status = insert_tweet(info.at(1))
#                        elif info.at(0) == "insert_tweet_session":
#                            status = insert_tweet_session(info.at(1),info.at(2),info.at(3),info.at(4),info.at(5))
#                        # elif ....
#                        if status == "Full":
#                            time.sleep(1)
#                    except FullQueue:
#                        time.sleep(1) # wait one second when the queue has data but connections are full.
#            time.sleep(5)


@app.route('/insert_timelines_attention', methods=['POST']) # Making this async would help alot but require 3 connections instead of one. Should work.
def insert_timelines_attention():
    start_time = time.time()
    payload = ""
    tries = 5 # perhaps move this to config file?
    connection = None
    try:
        #Getting connection from pool
        payload = request.json
    except:
        print("Failed to recieve the JSON package.") # Log this
        return None
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
        try: # Can wrap all 3 of these loops in their own try catch perhaps for better error handling/retries
            conn_cur = connection.cursor()
            # We can also async all 3 of these 
            for obj in payload[0]:
                tweet_id = obj['tweet_id']
                tweet_json = json.dumps(obj['tweet_json'])
                sql = """INSERT INTO tweet VALUES(%s,%s) ON CONFLICT DO NOTHING;"""
                conn_cur.execute(sql, (tweet_id,tweet_json))
            connection.commit()

            worker_id = payload[5]
            screenname = payload[6]

            #DELETE ATTENTION TABLES
            sql = """DELETE FROM user_home_timeline_chronological where user_id = %s"""
            conn_cur.execute(sql,(worker_id,))
            sql = """DELETE FROM user_home_timeline_control where user_id = %s"""
            conn_cur.execute(sql,(worker_id,))
            sql = """DELETE FROM user_tweet_attn_snapshot_chronological where user_id = %s"""
            conn_cur.execute(sql,(worker_id,))
            sql = """DELETE FROM user_tweet_attn_snapshot_control where user_id = %s"""
            conn_cur.execute(sql,(worker_id,))
            connection.commit()

            for obj in payload[1]: # Take care of tweet in session here.
                fav_before = obj['fav_before']
                tid = obj['tid']
                rtbefore = obj['rtbefore']
                page = obj['page']
                rank = str(obj['rank'])
                predicted_score = obj['predicted_score']
                sql = """INSERT INTO user_home_timeline_chronological(tweet_id,user_id,screenname,is_favorited_before,has_retweet_before,rank,page,last_updated,predicted_score)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
                now_session_start = datetime.datetime.now()
                session_start = now_session_start.strftime('%Y-%m-%d %H:%M:%S')
                #session_start = str(now_session_start.year) + '-' + str(now_session_start.month) + '-' + str(now_session_start.day) + ' ' + str(now_session_start.hour) + ':' + str(now_session_start.minute) + ':' + str(now_session_start.second)
                conn_cur.execute(sql,(tid,worker_id,screenname,fav_before,rtbefore,rank,page,session_start,predicted_score,))
            connection.commit()

            for obj in payload[3]: # Take care of tweet in session here.
                fav_before = obj['fav_before']
                tid = obj['tid']
                rtbefore = obj['rtbefore']
                page = obj['page']
                rank = str(obj['rank'])
                predicted_score = obj['predicted_score']
                sql = """INSERT INTO user_home_timeline_control(tweet_id,user_id,screenname,is_favorited_before,has_retweet_before,rank,page,last_updated,predicted_score)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
                now_session_start = datetime.datetime.now()
                session_start = now_session_start.strftime('%Y-%m-%d %H:%M:%S')
                #session_start = str(now_session_start.year) + '-' + str(now_session_start.month) + '-' + str(now_session_start.day) + ' ' + str(now_session_start.hour) + ':' + str(now_session_start.minute) + ':' + str(now_session_start.second)
                conn_cur.execute(sql,(tid,worker_id,screenname,fav_before,rtbefore,rank,page,session_start,predicted_score,))
            connection.commit()           

            for obj in payload[2]: # Take care of tweet in attention here.
                tweet_id = obj['tweet_id']
                page = str(obj['page'])
                rank = str(obj['rank'])
                present = obj['present']
                sql = """INSERT INTO user_tweet_attn_snapshot_chronological(tweet_id,user_id,page,rank,correct_ans) VALUES(%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(tweet_id,worker_id,page,rank,present,))
            connection.commit()

            for obj in payload[4]: # Take care of tweet in attention here.
                tweet_id = obj['tweet_id']
                page = str(obj['page'])
                rank = str(obj['rank'])
                present = obj['present']
                sql = """INSERT INTO user_tweet_attn_snapshot_control(tweet_id,user_id,page,rank,correct_ans) VALUES(%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(tweet_id,worker_id,page,rank,present,))
            connection.commit()

            conn_cur.close()
            accessPool.putconn(connection) #closing the connection
        except Exception as error:
            print(str(error) + " Something inside of the insertion failed.") # Log this.
    print("TOTAL RUN TIME: SYNCRONUS: " +str(time.time() - start_time) )
    return "Done" # make sure this doesnt have to be arbitrary text, none might cause an error?

@app.route('/insert_timelines_attention_in_session', methods=['GET','POST']) # Making this async would help alot but require 3 connections instead of one. Should work.
def insert_timelines_attention_in_session():
    start_time = time.time()
    payload = ""
    tries = 5 # perhaps move this to config file?
    connection = None
    try:
        #Getting connection from pool
        payload = request.json
    except:
        print("Failed to recieve the JSON package.") # Log this
        return None
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
        try: # Can wrap all 3 of these loops in their own try catch perhaps for better error handling/retries
            conn_cur = connection.cursor()

            session_id = payload[0]
            feedtype = payload[1]

            for obj in payload[2]: # Take care of tweet in session here.
                fav_before = obj['fav_before']
                tid = obj['tid']
                rtbefore = obj['rtbefore']
                page = obj['page']
                rank = str(obj['rank'])
                predicted_score = obj['predicted_score']
                sql = """INSERT INTO user_engagement_and_impression_session(tweet_id,session_id,is_favorited_before,has_retweet_before,rank,page,feedtype,predicted_score)
                VALUES(%s,%s,%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(tid,session_id,fav_before,rtbefore,rank,page,feedtype,predicted_score))
            connection.commit()

            for obj in payload[3]: # Take care of tweet in attention here.
                tweet_id = obj['tweet_id']
                page = str(obj['page'])
                rank = str(obj['rank'])
                present = obj['present']
                sql = """INSERT INTO user_tweet_attn_session(tweet_id,session_id,page,rank,correct_ans,feedtype) VALUES(%s,%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(tweet_id,session_id,page,rank,present,feedtype,))
            connection.commit()

            conn_cur.close()
            accessPool.putconn(connection) #closing the connection
            return jsonify(session_id=str(session_id))
        except Exception as error:
            print(str(error) + " Something inside of the insertion failed.") # Log this.
            return "Fail"
    print("TOTAL RUN TIME: SYNCRONUS: " +str(time.time() - start_time) )
    return "Done" # make sure this doesnt have to be arbitrary text, none might cause an error?

# Send me JSON with 2 arrays of arrays/objects. 0: tweets, 1: tweet_session. (I will get ID's for the other relation from 0) AND append the worker id as the 3rd "array/object"
# Essentially I want an array of "arrays" where the outer array has 3 elements and inside they have arrays of objects etc.
@app.route('/insert_tweet', methods=['POST']) # Making this async would help alot but require 3 connections instead of one. Should work.
def insert_tweet():
    start_time = time.time()
    payload = ""
    tries = 5 # perhaps move this to config file?
    connection = None
    favorite_now = False
    retweet_now = False
    try:
        #Getting connection from pool
        payload = request.json
    except:
        print("Failed to recieve the JSON package.") # Log this
        return None
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
        try: # Can wrap all 3 of these loops in their own try catch perhaps for better error handling/retries
            conn_cur = connection.cursor()
            # We can also async all 3 of these 
            for obj in payload[0]:
                tweet_id = obj['tweet_id']
                tweet_json = json.dumps(obj['tweet_json'])
                sql = """INSERT INTO tweet VALUES(%s,%s) ON CONFLICT DO NOTHING;"""
                conn_cur.execute(sql, (tweet_id,tweet_json))
            connection.commit()

            worker_id = payload[3]

            for obj in payload[1]: # Take care of tweet in session here.
                fav_before = obj['fav_before']
                tid = obj['tid']
                rtbefore = obj['rtbefore']
                page = obj['page']
                rank = str(obj['rank'])
                sql = """INSERT INTO user_tweet_association_and_engagements(tweet_id,user_id,is_favorited_before,has_retweet_before,tweet_retweeted,tweet_favorited,rank,page)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(tid,worker_id,fav_before,rtbefore,retweet_now,favorite_now,rank,page,))
            connection.commit()

            for obj in payload[2]: # Take care of tweet in attention here.
                tweet_id = obj['tweet_id']
                page = str(obj['page'])
                rank = str(obj['rank'])
                present = obj['present']
                sql = """INSERT INTO user_tweet_attn(tweet_id,user_id,page,rank,correct_ans) VALUES(%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(tweet_id,worker_id,page,rank,present,))
            connection.commit()

            conn_cur.close()
            accessPool.putconn(connection) #closing the connection
        except Exception as error:
            print(str(error) + " Something inside of the insertion failed.") # Log this.
    print("TOTAL RUN TIME: SYNCRONUS: " +str(time.time() - start_time) )
    return "Done" # make sure this doesnt have to be arbitrary text, none might cause an error?

@app.route('/insert_tweet_async', methods=['POST']) # Making this async would help alot but require 3 connections instead of one. Should work.
def insert_tweet_async():
    start_time = time.time()
    tries = 5
    try:
        #Getting connection from pool
        payload = request.json
    except:
        print("Failed to recieve the JSON package.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
        try:
            #cur1 = connection.cursor()
            #cur2 = connection.cursor()
            #cur3 = connection.cursor()
            #tasks = []
            #loop = asyncio.get_event_loop()
            #tasks.append(loop.create_task(insert_async_tweet(payload[0],cur1)))
            #tasks.append(loop.create_task(user_tweet_ass(payload[0],payload[2]["worker_id"], cur2)))            
            #tasks.append(loop.create_task(tweet_session(payload[1],cur3)))
            #loop.run_until_complete(main())
            #loop.run_until_complete(asyncio.wait(tasks))
            asyncio.run(run_tasks(payload,connection))

        
        except Exception as error:
            print("Big issue: " + str(error))

    print("TOTAL RUN TIME: ASYNCRONUS: " +str(time.time() - start_time) )
    return "Done"

async def run_tasks(payload,connection):
    cur1 = connection.cursor()
    cur2 = connection.cursor()
    cur3 = connection.cursor()
    await asyncio.gather (
        insert_async_tweet(payload[0],cur1),
        user_tweet_ass(payload[0],payload[2], cur2),
        tweet_session(payload[1],cur3)
    )
    connection.commit()
    cur1.close()
    cur2.close()
    cur3.close()
    accessPool.putconn(connection)

async def insert_async_tweet(tweets, conn_cur) -> None:
    for obj in tweets:
        tweet_id = obj['tweet_id']
        sql = """INSERT INTO tweet(tweet_id) VALUES(%s) ON CONFLICT DO NOTHING;"""
        conn_cur.execute(sql, (tweet_id,))

async def user_tweet_ass(tweets, worker_id, conn_cur) -> None:
    for obj in tweets: # User_tweet_ass
        tweet_id = obj['tweet_id']
        sql = """INSERT INTO user_tweet_ass(tweet_id,worker_id) VALUES(%s,%s) ON CONFLICT DO NOTHING;"""
        conn_cur.execute(sql, (tweet_id,worker_id))     

async def tweet_session(tweets, conn_cur) -> None:
    favorite_now = False
    retweet_now = False
    tweet_seen = False
    for obj in tweets: # Take care of tweet in session here.
        fav_before = obj['fav_before']
        sid = obj['sid']
        tid = obj['tid']
        rtbefore = obj['rtbefore']
        rank = obj['rank']
        sql = """INSERT INTO tweet_in_session(is_favorited_before,session_id,tweet_id,has_retweet_before,tweet_seen,tweet_retweeted,tweet_favorited,rank)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s);"""
        conn_cur.execute(sql,(fav_before,sid,tid,rtbefore,tweet_seen,retweet_now,favorite_now,rank,))


@app.route('/get_existing_mturk_user', methods=['GET','POST']) # Should the method be GET?
def get_existing_mturk_user():
    tries = 5
    connection = None
    worker_id = ''
    worker_id = request.args.get('worker_id').strip()
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        sql = """SELECT U.access_token,U.access_token_secret,U.screenname,U.twitter_id,M.participant_id,M.assignment_id,M.project_id FROM rockwell_user U, mturk_user M 
        WHERE M.id = U.mturk_ref_id and U.user_id = %s"""
        conn_cur.execute(sql, (worker_id,))     
        ret = conn_cur.fetchall()
        conn_cur.close()
        accessPool.putconn(connection)
        return jsonify(data=ret)
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/get_existing_user', methods=['GET','POST']) # Should the method be GET?
def get_worker_credentials():
    tries = 5
    connection = None
    worker_id = ''
    worker_id = request.args.get('worker_id').strip()
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        sql = """SELECT U.access_token,U.access_token_secret,U.screenname,U.twitter_id FROM rockwell_user U WHERE U.user_id = %s"""
        conn_cur.execute(sql, (worker_id,))     
        ret = conn_cur.fetchall()
        conn_cur.close()
        accessPool.putconn(connection)
        return jsonify(data=ret)
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/get_existing_tweets_new', methods=['GET','POST'])
def get_worker_tweet_chronological():
    tries = 5
    connection = None
    worker_id = ''
    page = ''
    feedtype = ''
    worker_id = request.args.get('worker_id').strip()
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
        page = request.args.get('page').strip()
        feedtype = request.args.get('feedtype').strip()
        print("Worker ID : "+worker_id)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        if feedtype == 'S':
            if page == 'NA':
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,UA.page,UA.rank,T.tweet_json FROM user_home_timeline_chronological UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s"""
                conn_cur.execute(sql, (worker_id,))
            else:
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,T.tweet_json FROM user_home_timeline_chronological UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s AND UA.page = %s"""
                conn_cur.execute(sql, (worker_id,page))
        elif feedtype == 'M':
            if page == 'NA':
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,UA.page,UA.rank,T.tweet_json FROM user_home_timeline_control UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s"""
                conn_cur.execute(sql, (worker_id,))
            else:
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,T.tweet_json FROM user_home_timeline_control UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s AND UA.page = %s"""
                conn_cur.execute(sql, (worker_id,page))     
        if conn_cur.rowcount > 0:
            ret = conn_cur.fetchall()
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data=ret)
        else:
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data="NEW") #Meaning we need to fetch new tweets.
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/get_existing_tweets_new_screenname', methods=['GET','POST'])
def get_existing_tweets_new_screenname():
    tries = 5
    connection = None
    screenname = ''
    page = ''
    feedtype = ''
    screenname = request.args.get('screenname').strip()
    try:
        #Getting connection from pool
        screenname = request.args.get('screenname').strip()
        page = request.args.get('page').strip()
        feedtype = request.args.get('feedtype').strip()
    except:
        print("Failed to recieve the screenname.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        if feedtype == 'S':
            if page == 'NA':
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,UA.page,UA.rank,T.tweet_json,UA.user_id FROM user_home_timeline_chronological UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.screenname = %s"""
                conn_cur.execute(sql, (screenname,))
            else:
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,T.tweet_json,UA.user_id FROM user_home_timeline_chronological UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.screenname = %s AND UA.page = %s"""
                conn_cur.execute(sql, (screenname,page))
        elif feedtype == 'M':
            if page == 'NA':
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,UA.page,UA.rank,T.tweet_json,UA.user_id FROM user_home_timeline_control UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.screenname = %s"""
                conn_cur.execute(sql, (screenname,))
            else:
                sql = """SELECT UA.tweet_id,UA.last_updated,UA.is_favorited_before,UA.has_retweet_before,T.tweet_json,UA.user_id FROM user_home_timeline_control UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.screenname = %s AND UA.page = %s"""
                conn_cur.execute(sql, (screenname,page))     
        if conn_cur.rowcount > 0:
            ret = conn_cur.fetchall()
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data=ret)
        else:
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data="NEW") #Meaning we need to fetch new tweets.
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/get_existing_attn_tweets_new', methods=['GET','POST'])
def get_existing_tweets_attn_chronological():
    tries = 5
    connection = None
    worker_id = ''
    page = ''
    feedtype = ''
    worker_id = request.args.get('worker_id').strip()
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
        page = request.args.get('page').strip()
        feedtype = request.args.get('feedtype').strip()
        print("Worker ID : "+worker_id)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        if feedtype == 'S':
            if page == 'NA':
                sql = """SELECT UA.tweet_id,UA.correct_ans,UA.page,UA.rank,T.tweet_json FROM user_tweet_attn_snapshot_chronological UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s"""
                conn_cur.execute(sql, (worker_id,))
            else:
                sql = """SELECT UA.tweet_id,UA.correct_ans,T.tweet_json FROM user_tweet_attn_snapshot_chronological UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s AND UA.page = %s"""
                conn_cur.execute(sql, (worker_id,page))     
        elif feedtype == 'M':
            if page == 'NA':
                sql = """SELECT UA.tweet_id,UA.correct_ans,UA.page,UA.rank,T.tweet_json FROM user_tweet_attn_snapshot_control UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s"""
                conn_cur.execute(sql, (worker_id,))
            else:
                sql = """SELECT UA.tweet_id,UA.correct_ans,T.tweet_json FROM user_tweet_attn_snapshot_control UA,tweet T 
                WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s AND UA.page = %s"""
                conn_cur.execute(sql, (worker_id,page))
        if conn_cur.rowcount > 0:
            ret = conn_cur.fetchall()
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data=ret)
        else:
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data="NEW") #Meaning we need to fetch new tweets.
    except Exception as error:
        print(error)
    return "Done!"

# New functions for the checking of existing tweets for a worker_id tweet_id relationship.

@app.route('/get_existing_tweets', methods=['GET','POST']) # Should the method be GET?
def get_worker_tweet():
    print("In get existing tweets")
    tries = 5
    connection = None
    worker_id = ''
    page = ''
    worker_id = request.args.get('worker_id').strip()
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
        page = request.args.get('page').strip()
        print("Worker ID : "+worker_id)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        sql = """SELECT UA.tweet_id,T.tweet_json FROM user_tweet_association_and_engagements UA,tweet T 
        WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s AND UA.page = %s"""
        conn_cur.execute(sql, (worker_id,page))     
        if conn_cur.rowcount > 0:
            ret = conn_cur.fetchall()
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data=ret)
        else:
            conn_cur.close()
            accessPool.putconn(connection)
            return jsonify(data="NEW") #Meaning we need to fetch new tweets.
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/get_existing_attn_tweets', methods=['GET','POST']) # Should the method be GET?
def get_worker_attention_tweet():
    print("In get existing attention tweets")
    tries = 5
    connection = None
    worker_id = ''
    page = ''
    worker_id = request.args.get('worker_id').strip()
    print("Worker Id in attention check : "+str(worker_id))
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
        page = request.args.get('page').strip()
        print("Worker ID : "+worker_id)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    #try:
    conn_cur = connection.cursor()
    sql = """SELECT UA.tweet_id,T.tweet_json FROM user_tweet_attn UA,tweet T 
    WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s AND UA.page = %s"""
    conn_cur.execute(sql, (worker_id,page,))     
    if conn_cur.rowcount > 0:
        ret = conn_cur.fetchall()
        conn_cur.close()
        accessPool.putconn(connection)
        return jsonify(data=ret)
    else:
        conn_cur.close()
        accessPool.putconn(connection)
        return jsonify(data="NEW") #Meaning we need to fetch new tweets.
    #except Exception as error:
    #    print("Error in get existing tweets!!!")
    #    print(error)
    return "Done!"    

@app.route('/engagements_save', methods=['GET','POST']) # Should the method be GET?
def save_all_engagements_new():
    tries = 5
    connection = None
    worker_id = 0
    page = 0
    try:
        session_id = request.args.get('session_id')
        #worker_id = int(request.args.get('worker_id'))
        page = int(request.args.get('page'))
        tweetRetweets = request.args.get('tweetRetweets')
        tweetLikes = request.args.get('tweetLikes')
        tweetViewTimeStamps = request.args.get('tweetViewTimeStamps')
        tweetLinkClicks = request.args.get('tweetLinkClicks')
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    try:
        while(tries > 0):
            connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
            if connection is None:
                time.sleep(0.2)
                tries = tries - 1
                continue
            tries = -1
        conn_cur = connection.cursor()
        sql_retweet = """UPDATE user_engagement_and_impression_session 
        SET tweet_retweeted = %s WHERE session_id = %s and page = %s and rank = %s"""
        sql_like = """UPDATE user_engagement_and_impression_session 
        SET tweet_favorited = %s WHERE session_id = %s and page = %s and rank = %s"""
        sql_telemetry = """UPDATE user_engagement_and_impression_session 
        SET seen_timestamp = %s WHERE session_id = %s and page = %s and rank = %s"""
        sql_inactivity = """INSERT INTO user_inactivity(session_id,tab_inactive_timestamp,tab_active_timestamp,page) values(%s,%s,%s,%s);"""
        sql_link_click = """INSERT INTO click(tweet_id,url,is_card,click_timestamp,session_id) values(%s,%s,%s,%s,%s);"""
        if len(tweetRetweets) > 0:
            for tweet_rank in tweetRetweets.split(','):
                conn_cur.execute(sql_retweet,(True,session_id,page,tweet_rank))
        if len(tweetLikes) > 0:
            for tweet_rank in tweetLikes.split(','):
                conn_cur.execute(sql_like,(True,session_id,page,tweet_rank))
        if len(tweetViewTimeStamps) > 0:
            timeStampsMap = tweetViewTimeStamps.split(',')
            tab_inactive = []
            tab_active = []
            for i in range(0,len(timeStampsMap),2):
                if timeStampsMap[i] == '-1':
                    tab_inactive.append(int(timeStampsMap[i+1]))
                if timeStampsMap[i] == '-2':
                    tab_active.append(int(timeStampsMap[i+1]))
                conn_cur.execute(sql_telemetry,(int(timeStampsMap[i+1]),session_id,page,timeStampsMap[i]))
            print("TAB ACTIVE : ")
            print(tab_active)
            if len(tab_inactive) > 0:
                for i in range(len(tab_inactive)):
                    conn_cur.execute(sql_inactivity,(session_id,tab_inactive[i],tab_active[i],page))
        if len(tweetLinkClicks) > 0:
            tweetLinkClickMap = tweetLinkClicks.split(',')
            for i in range(0,len(tweetLinkClickMap),4):
                conn_cur.execute(sql_link_click,(int(tweetLinkClickMap[i+1]),tweetLinkClickMap[i],tweetLinkClickMap[i+2],tweetLinkClickMap[i+3],session_id))
        connection.commit()
        conn_cur.close()
        accessPool.putconn(connection) #closing the connection
    except Exception as error:
        print(str(error) + " Something inside of the insertion failed.") # Log this.
        return "Failed"
    return "Done!"

@app.route('/engagements_save_prev_2', methods=['GET','POST']) # Should the method be GET?
def save_all_engagements_new_old():
    tries = 5
    connection = None
    worker_id = 0
    page = 0
    try:
        random_indentifier = request.args.get('random_indentifier')
        worker_id = worker_id_store[random_indentifier]
        del worker_id_store[random_indentifier]
        #worker_id = int(request.args.get('worker_id'))
        page = int(request.args.get('page'))
        tweetRetweets = request.args.get('tweetRetweets')
        tweetLikes = request.args.get('tweetLikes')
        tweetViewTimeStamps = request.args.get('tweetViewTimeStamps')
        tweetLinkClicks = request.args.get('tweetLinkClicks')
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    try:
        while(tries > 0):
            connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
            if connection is None:
                time.sleep(0.2)
                tries = tries - 1
                continue
            tries = -1
        conn_cur = connection.cursor()
        sql_retweet = """UPDATE user_tweet_association_and_engagements 
        SET tweet_retweeted = %s WHERE user_id = %s and page = %s and rank = %s"""
        sql_like = """UPDATE user_tweet_association_and_engagements 
        SET tweet_favorited = %s WHERE user_id = %s and page = %s and rank = %s"""
        sql_telemetry = """UPDATE user_tweet_association_and_engagements 
        SET seen_timestamp = %s WHERE user_id = %s and page = %s and rank = %s"""
        sql_inactivity = """INSERT INTO user_inactivity(user_id,tab_inactive_timestamp,tab_active_timestamp,page) values(%s,%s,%s,%s);"""
        sql_link_click = """INSERT INTO click(tweet_id,url,is_card,click_timestamp,user_id) values(%s,%s,%s,%s,%s);"""
        if len(tweetRetweets) > 0:
            for tweet_rank in tweetRetweets.split(','):
                conn_cur.execute(sql_retweet,(True,worker_id,page,tweet_rank))
        if len(tweetLikes) > 0:
            for tweet_rank in tweetLikes.split(','):
                conn_cur.execute(sql_like,(True,worker_id,page,tweet_rank))
        if len(tweetViewTimeStamps) > 0:
            timeStampsMap = tweetViewTimeStamps.split(',')
            tab_inactive = []
            tab_active = []
            for i in range(0,len(timeStampsMap),2):
                if timeStampsMap[i] == '-1':
                    tab_inactive.append(int(timeStampsMap[i+1]))
                if timeStampsMap[i] == '-2':
                    tab_active.append(int(timeStampsMap[i+1]))
                conn_cur.execute(sql_telemetry,(int(timeStampsMap[i+1]),worker_id,page,timeStampsMap[i]))
            print("TAB ACTIVE : ")
            print(tab_active)
            if len(tab_inactive) > 0:
                for i in range(len(tab_inactive)):
                    conn_cur.execute(sql_inactivity,(worker_id,tab_inactive[i],tab_active[i],page))
        if len(tweetLinkClicks) > 0:
            tweetLinkClickMap = tweetLinkClicks.split(',')
            for i in range(0,len(tweetLinkClickMap),4):
                conn_cur.execute(sql_link_click,(int(tweetLinkClickMap[i+1]),tweetLinkClickMap[i],tweetLinkClickMap[i+2],tweetLinkClickMap[i+3],worker_id))
        connection.commit()
        conn_cur.close()
        accessPool.putconn(connection) #closing the connection
    except Exception as error:
        print(str(error) + " Something inside of the insertion failed.") # Log this.
        return "Failed"
    return "Done!"

@app.route('/attention_save', methods=['GET','POST']) # Should the method be GET?
def save_all_attention_new():
    tries = 5
    connection = None
    try:
        session_id = request.args.get('session_id')
        page = int(request.args.get('page'))
        attnanswers = request.args.get('attnanswers')
        print(attnanswers)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    try:
        while(tries > 0):
            connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
            if connection is None:
                time.sleep(0.2)
                tries = tries - 1
                continue
            tries = -1
        conn_cur = connection.cursor()
        sql_attn_answers = """UPDATE user_tweet_attn_session SET given_ans = %s where session_id = %s and page = %s and rank = %s"""
        answers = attnanswers.split(',')
        for (rankk,ans) in enumerate(answers):
            bool_answer = False
            if ans == '1':
                bool_answer = True
            conn_cur.execute(sql_attn_answers,(bool_answer,session_id,page,int(rankk)))
        connection.commit()
        conn_cur.close()
        accessPool.putconn(connection) #closing the connection
    except Exception as error:
        print(str(error) + " Something inside of the insertion failed.") # Log this.
        return "Failed"
    return "Done!"

@app.route('/attention_save_prev', methods=['GET','POST']) # Should the method be GET?
def save_all_attention_new_prev():
    tries = 5
    connection = None
    try:
        random_indentifier = request.args.get('random_indentifier')
        worker_id = worker_id_store[random_indentifier]
        del worker_id_store[random_indentifier]
        #worker_id = int(request.args.get('worker_id'))
        page = int(request.args.get('page'))
        attnanswers = request.args.get('attnanswers')
        print(attnanswers)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    try:
        while(tries > 0):
            connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
            if connection is None:
                time.sleep(0.2)
                tries = tries - 1
                continue
            tries = -1
        conn_cur = connection.cursor()
        sql_attn_answers = """UPDATE user_tweet_attn SET given_ans = %s where user_id = %s and page = %s and rank = %s"""
        answers = attnanswers.split(',')
        for (rankk,ans) in enumerate(answers):
            bool_answer = False
            if ans == '1':
                bool_answer = True
            conn_cur.execute(sql_attn_answers,(bool_answer,worker_id,page,int(rankk)))
        connection.commit()
        conn_cur.close()
        accessPool.putconn(connection) #closing the connection
    except Exception as error:
        print(str(error) + " Something inside of the insertion failed.") # Log this.
        return "Failed"
    return "Done!"


@app.route('/engagements_save_prev', methods=['POST']) # Should the method be GET?
def save_all_engagements():
    tries = 5
    connection = None
    worker_id = ''
    refreshh = ''
    retweet_map = ''
    like_map = ''
    seen_map = ''
    click_map_url = ''
    try:
        #Getting connection from pool
        payload = request.get_json()
        worker_id = payload['worker_id']
        retweet_map = payload['retweet_map']
        like_map = payload['like_map']
        seen_map = payload['seen_map']
        click_map_url = payload['click_map']
        print("seen_map")
        print(seen_map)
        print(click_map_url)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn() # I dont believe this can throw an error. Need confirmation, if it can, try catch wrap.
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        sql = """UPDATE user_tweet_ass 
        SET tweet_seen = %s, tweet_retweeted = %s, tweet_favorited = %s 
        WHERE worker_id = %s and refreshh = %s and rank = %s"""
        for refreshh in range(len(retweet_map)):
            retweet_map_int = retweet_map[refreshh].split(',')
            like_map_int = like_map[refreshh].split(',')
            seen_map_int = seen_map[refreshh].split(',')
            for rank in range(len(retweet_map_int)):
                conn_cur.execute(sql,(bool(int(seen_map_int[rank])),bool(int(retweet_map_int[rank])),bool(int(like_map_int[rank])),worker_id,refreshh,rank+1))
        sql_click = """INSERT INTO click(tweet_id,url,is_card,click_timestamp,worker_id)
        VALUES(%s,%s,%s,%s,%s);"""     
        for clickk_each in click_map_url:
            clickk = clickk_each.split(",")
            for cc in clickk:
                cc_comp = cc.split(";")
                click_timestamp = cc_comp[3]
                formatt = '%m/%d/%Y  %I:%M:%S %p'
                click_datetime = datetime.datetime.strptime(click_timestamp,formatt)
                conn_cur.execute(sql_click,(cc_comp[0],cc_comp[1],cc_comp[2],click_timestamp,worker_id)) 
        connection.commit()
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/insert_session', methods=['GET'])
def insert_session():
    """ insert a new vendor into the vendors table """
    retVal123 = -1
    #sql = """INSERT INTO rockwell_user(user_id,yougov_ref_id,mturk_ref_id,twitter_id,access_token,access_token_secret,screenname,session_start,account_settings)
    #     VALUES(%s,1,1,%s,%s,%s,%s,%s,%s) RETURNING user_id;"""
    sql = """INSERT INTO session_table(user_id,session_start) VALUES(%s,%s) RETURNING session_id;"""
    try:
        connection = accessPool.getconn()
        if connection is not False: 
            worker_id = request.args.get('worker_id')
            now_session_start = datetime.datetime.now()
            session_start = now_session_start.strftime('%Y-%m-%d %H:%M:%S')
            cursor = connection.cursor()
            cursor.execute(sql, (worker_id,session_start,))
            retVal123 = cursor.fetchall()[0][0]
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
            return jsonify(data=retVal123)
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)
    return retVal123

@app.route('/insert_mturk_user', methods=['GET'])
def insert_mturk_user():
    """ insert a new vendor into the vendors table """
    retVal123 = -1
    sql = """INSERT INTO mturk_user(participant_id,assignment_id,project_id) VALUES(%s,%s,%s) RETURNING id;"""
    try:
        connection = accessPool.getconn()
        if connection is not False: 
            participant_id = request.args.get('participant_id')
            assignment_id = request.args.get('assignment_id')
            project_id = request.args.get('project_id')
            cursor = connection.cursor()
            cursor.execute(sql, (participant_id,assignment_id,project_id,))
            retVal123 = cursor.fetchall()[0][0]
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
            return jsonify(data=retVal123)
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)
    return retVal123

@app.route('/insert_user', methods=['GET'])
def insert_user():
    """ insert a new vendor into the vendors table """
    retVal123 = -1
    #sql = """INSERT INTO rockwell_user(user_id,yougov_ref_id,mturk_ref_id,twitter_id,access_token,access_token_secret,screenname,session_start,account_settings)
    #     VALUES(%s,1,1,%s,%s,%s,%s,%s,%s) RETURNING user_id;"""
    sql = """INSERT INTO rockwell_user(user_id,yougov_ref_id,mturk_ref_id,twitter_id,access_token,access_token_secret,screenname,account_settings)
          VALUES(%s,1,%s,%s,%s,%s,%s,%s);"""
    try:
        connection = accessPool.getconn()
        if connection is not False:
            mturk_ref_id = request.args.get('mturk_ref_id')
            twitter_id = request.args.get('twitter_id')
            access_token = request.args.get('access_token')
            access_token_secret = request.args.get('access_token_secret')
            screenname = request.args.get('screenname')
            account_settings_json = json.dumps(request.args.get('account_settings'))
            now_session_start = datetime.datetime.now()
            session_start = str(now_session_start.year) + '-' + str(now_session_start.month) + '-' + str(now_session_start.day) + ' ' + str(now_session_start.hour) + ':' + str(now_session_start.minute) + ':' + str(now_session_start.second)
            print("INSERTTT USER DATEEEEEE")
            print(session_start)
            random_identifier = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
            cursor = connection.cursor()
            cursor.execute(sql, (random_identifier,mturk_ref_id,twitter_id,access_token,access_token_secret,screenname,account_settings_json,))
            #retVal123 = cursor.fetchall()[0][0]
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
            return jsonify(data=random_identifier)
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)
    return retVal123


#@app.route('/insert_user_tweet_ass', methods=['POST'])
#def insert_usert_tweet():
#    try:
#        #Getting connection from pool
#        connection = accessPool.getconn()
#        if connection is not False:
#            now = datetime.datetime.now() what was all this?
#            time = now.year + '-' + now.month + '-' + now.day + ' ' + now.hour + ':' + now.minute + ':' + now.second
#            worker_id = request.args.get('worker_id')
#            tweet_id = reqest.args.get('tweet_id')
#            sql = """INSERT INTO user_tweet_ass(tweet_id,worker_id,)
#                VALUES(%s,%s) RETURNING session_id;"""
#            cursor = connection.cursor()
#            cursor.execute(sql,(tweet_id,worker_id,))
#            cursor.close()
#            accessPool.putconn(connection)
#    except (Exception, psycopg2.DatabaseError) as error:
#        print("ERROR!!!!",error)

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    #await queueLoop()
    app.run(host = "0.0.0.0", port = 5052)
