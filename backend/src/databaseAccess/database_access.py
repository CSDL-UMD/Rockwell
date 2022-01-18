from flask import Flask, render_template, request, url_for, jsonify
import json
from src.databaseAccess.database_config import config
import psycopg2
from psycopg2 import pool
import datetime
import time
import asyncio

#Global pool variable:
pool_is_full = False

universal_buffer = []
params = config('../configuration/config.ini','postgresql')
MIN = params['min']
MAX = params['max']
accessPool =  psycopg2.pool.SimpleConnectionPool(MIN, MAX,host=params["host"],database=params["database"],user=params["user"],password=params["password"],port=params["port"])# Maybe make 2 pools and half the functions use each or make this one huge.
print("Access Pool object")
print(accessPool)
app = Flask(__name__)

app.debug = False

@app.route('/insert_tweet', methods=['POST']) # Making this async would help alot but require 3 connections instead of one. Should work.
def insert_tweet():
    start_time = time.time()
    payload = ""
    tries = 5 # perhaps move this to config file?
    connection = None
    favorite_now = False
    retweet_now = False
    tweet_seen = None
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
                sql = """INSERT INTO tweet VALUES(%s,%s,%s) ON CONFLICT DO NOTHING;"""
                conn_cur.execute(sql, (tweet_id,tweet_json,False))
            connection.commit()

            worker_id = payload[3]

            for obj in payload[1]: # Take care of tweet in session here.
                fav_before = obj['fav_before']
                tid = obj['tid']
                rtbefore = obj['rtbefore']
                rank = str(obj['rank'])
                tweet_min = obj['tweet_min']
                tweet_max = obj['tweet_max']
                refreshh = obj['refresh']
                sql = """INSERT INTO user_tweet_ass(tweet_id,user_id,is_favorited_before,has_retweet_before,tweet_seen,tweet_retweeted,tweet_favorited,tweet_min,tweet_max,refreshh,rank)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(tid,worker_id,fav_before,rtbefore,tweet_seen,retweet_now,favorite_now,tweet_min,tweet_max,refreshh,rank,))
            connection.commit()

            for obj in payload[2]: # Take care of tweet in attention here.
                tweet_id = obj['tweet_id']
                rank = str(obj['rank'])
                sql = """INSERT INTO user_tweet_attn(tweet_id,user_id,rank) VALUES(%s,%s,%s);"""
                conn_cur.execute(sql,(tweet_id,worker_id,rank,))
            connection.commit()

            conn_cur.close()
            accessPool.putconn(connection) #closing the connection
        except Exception as error:
            print(str(error) + " Something inside of the insertion failed.") # Log this.
    print("TOTAL RUN TIME: SYNCRONUS: " +str(time.time() - start_time) )
    return "Done" # make sure this doesnt have to be arbitrary text, none might cause an error?

@app.route('/insert_prereg', methods=['POST']) # Making this async would help alot but require 3 connections instead of one. Should work.
def insert_prereg():
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
                sql = """INSERT INTO tweet VALUES(%s,%s,%s) ON CONFLICT DO NOTHING;"""
                conn_cur.execute(sql, (tweet_id,tweet_json,False))
            connection.commit()

            worker_id = payload[4]

            for i in range(1,4):
                for obj in payload[i]: # Take care of tweet in session here.
                    tweet_id = obj['tweet_id']
                    rank = obj['rank']
                    attnlevel = obj['attnlevel']
                    present = obj['present']
                    sql = """INSERT INTO prereg_attn(tweet_id,worker_id,rank,attnlevel,present) VALUES(%s,%s,%s,%s,%s);"""
                    conn_cur.execute(sql,(tweet_id,worker_id,rank,attnlevel,present,))
                connection.commit()
            conn_cur.close()
            accessPool.putconn(connection) #closing the connection
        except Exception as error:
            print(str(error) + " Something inside of the insertion failed.") # Log this.
    return "Done"

# New functions for the checking of existing tweets for a worker_id tweet_id relationship.

@app.route('/get_existing_tweets', methods=['GET','POST'])
def get_worker_tweet():
    tries = 5
    connection = None
    worker_id = ''
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
        print("Worker ID : "+worker_id)
    except:
        print("Failed to recieve the worker id.")
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn()
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    try:
        conn_cur = connection.cursor()
        sql = """SELECT UA.tweet_id,UA.tweet_min,UA.tweet_max,UA.refreshh,T.tweet_json FROM user_tweet_ass UA,tweet T 
        WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s AND UA.refreshh = (SELECT MAX(refreshh) from user_tweet_ass where user_id = %s)"""
        conn_cur.execute(sql, (worker_id,worker_id))     
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

@app.route('/get_existing_attn_tweets', methods=['GET','POST'])
def get_worker_attention_tweet():
    tries = 5
    connection = None
    worker_id = ''
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
        print("Worker ID : "+worker_id)
    except:
        print("Failed to recieve the worker id.")
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn()
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    #try:
    conn_cur = connection.cursor()
    sql = """SELECT UA.tweet_id,T.tweet_json FROM user_tweet_attn UA,tweet T 
    WHERE T.tweet_id = UA.tweet_id AND UA.user_id = %s"""
    conn_cur.execute(sql, (worker_id,))     
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

@app.route('/get_prereg_tweets', methods=['GET','POST'])
def get_prereg_tweets():
    tries = 5
    connection = None
    worker_id = ''
    try:
        #Getting connection from pool
        worker_id = request.args.get('worker_id').strip()
        attnlevel = request.args.get('attnlevel').strip()
        print("Worker ID : "+worker_id)
        print("attnlevel : "+attnlevel)
    except:
        print("Failed to recieve the worker id.") # Log this
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn()
        if connection is None:
            time.sleep(0.2)
            tries = tries - 1
            continue
        tries = -1
    #try:
    conn_cur = connection.cursor()
    sql = """SELECT UA.tweet_id,UA.present,T.tweet_json FROM prereg_attn UA,tweet T 
    WHERE T.tweet_id = UA.tweet_id AND UA.worker_id = %s AND UA.attnlevel=%s"""
    conn_cur.execute(sql, (worker_id,attnlevel,))     
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

@app.route('/set_deleted_tweets', methods=['POST']) 
def set_deleted_tweets():
    connection = None
    try:
        connection = accessPool.getconn()
        if connection is not False:
            payload = request.json
            conn_cur = connection.cursor()
            for obj in payload:
                tweet_id = obj['del_tweet']
                sql = """UPDATE tweet SET tweet_deleted = %s WHERE tweet_id = %s"""
                conn_cur.execute(sql, (True,tweet_id))
            connection.commit()
    except Exception as error:
        print(error)
    return "Done"
#@app.route('/insert_tweet_session', methods=['POST'])
#def insert_tweet_session(): # This will take many arguments and takes logic in the guest access twitter to work
#    favorite_now = False
#    retweet_now = False
#    tweet_seen = False
#    connection = None
#    try:
#        #Getting connection from pool
#        connection = accessPool.getconn()
#        if connection is not False:
#            payload = request.json
#            cursor = connection.cursor()
#            for obj in payload:
#                # continue here
#                fav_before = obj['fav_before']
#                sid = obj['sid']
#                tid = obj['tid']
#                rtbefore = obj['rtbefore']
#                rank = obj['rank']
#                sql = """INSERT INTO tweet_in_session(is_favorited_before,session_id,tweet_id,has_retweet_before,tweet_seen,tweet_retweeted,tweet_favorited,rank)
#                VALUES(%s,%s,%s,%s,%s,%s,%s,%s);"""
#                cursor.execute(sql,(fav_before,sid,tid,rtbefore,tweet_seen,retweet_now,favorite_now,rank,))
#                #returnData = cursor.fetchall()
#                connection.commit()
#            cursor.close()
#            accessPool.putconn(connection) #closing the connection
#        else:   #Indicates the pool is full
#            print("Coming here")
#            data = []
#            data.append("insert_tweet_session")
#            data.append(fav_before)
#            data.append(sid)
#            data.append(tid)
#            data.append(rtbefore)
#            data.append(rank)
#            universal_buffer.append(data) # offload it to the queue.
#            #return "Full"
#    except Exception as error:
#        print(error)
#    return "Done!"

@app.route('/tracking_save', methods=['POST'])
def save_tracking():
    tries = 5
    connection = None
    worker_id = ''
    


@app.route('/engagements_save', methods=['POST'])
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
        print("Failed to recieve the worker id.")
        return "Failed"
    while(tries > 0):
        connection = accessPool.getconn()
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

@app.route('/update_tweet_retweet', methods=['POST'])
def update_tweet_retweet():
    connection = None
    try:
        connection = accessPool.getconn()
        if connection is not False:
            session_id = request.args.get('session_id')
            tweet_id = request.args.get('tweet_id')
            sql = """UPDATE tweet_in_session SET tweet_retweeted = %s WHERE session_id = %s and tweet_id = %s"""
            cursor = connection.cursor()
            cursor.execute(sql,(str(True),session_id,tweet_id,))
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/update_tweet_like', methods=['POST'])
def update_tweet_like():
    connection = None
    try:
        connection = accessPool.getconn()
        if connection is not False:
            session_id = request.args.get('session_id')
            tweet_id = request.args.get('tweet_id')
            sql = """UPDATE tweet_in_session SET tweet_favorited = %s WHERE session_id = %s and tweet_id = %s"""
            cursor = connection.cursor()
            cursor.execute(sql,(str(True),session_id,tweet_id,))
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/insert_user', methods=['GET'])
def insert_user():
    """ insert a new vendor into the vendors table """
    retVal123 = -1
    sql = """INSERT INTO rockwell_user(twitter_id,session_start,account_settings)
         VALUES(%s,%s,%s) RETURNING user_id;"""
    try:
        connection = accessPool.getconn()
        if connection is not False: 
            twitter_id = request.args.get('twitter_id')
            account_settings_json = json.dumps(request.args.get('account_settings'))
            now_session_start = datetime.datetime.now()
            session_start = str(now_session_start.year) + '-' + str(now_session_start.month) + '-' + str(now_session_start.day) + ' ' + str(now_session_start.hour) + ':' + str(now_session_start.minute) + ':' + str(now_session_start.second)
            cursor = connection.cursor()
            cursor.execute(sql, (twitter_id,session_start,account_settings_json,))
            retVal123 = cursor.fetchall()[0][0]
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
            return jsonify(data=retVal123)
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
    app.run(host = "0.0.0.0", port = 5052)