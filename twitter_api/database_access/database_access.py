from flask import Flask, render_template, request, url_for, jsonify
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
params = config('../../config.ini','postgresql')
accessPool =  psycopg2.pool.SimpleConnectionPool(MIN, MAX,host=params["host"],database=params["database"],user=params["user"],password=params["password"],port=params["port"])# Maybe make 2 pools and half the functions use each or make this one huge.
print("Access Pool object")
print(accessPool)
app = Flask(__name__)

app.debug = False
"""
Could do one main flask function here and then sub functions.
Each call will be put on a (global) queue with the function and the arguments.
The function would constantly add to the queue as requests come.
Then we would have a system that calls the function and passes the arguments when there is pool openings. 
We would then have a constantly running dequeue function that makes the calls unloading the queue untill it hits a limit, 
(functions would throw the error before popping the queue so its not deleted) then it waits a few seconds and begins calling again.
All of this should be done in this file. (async function called on start with a main loop.)
"""

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
    tweet_seen = False
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
                sql = """INSERT INTO tweet(tweet_id) VALUES(%s) ON CONFLICT DO NOTHING;"""
                conn_cur.execute(sql, (tweet_id,))
            connection.commit()
            worker_id = payload[2]
            for obj in payload[0]: # User_tweet_ass
                tweet_id = obj['tweet_id']
                sql = """INSERT INTO user_tweet_ass(tweet_id,worker_id) VALUES(%s,%s) ON CONFLICT DO NOTHING;"""
                conn_cur.execute(sql, (tweet_id,worker_id))            
            connection.commit()

            for obj in payload[1]: # Take care of tweet in session here.
                fav_before = obj['fav_before']
                sid = obj['sid']
                tid = obj['tid']
                rtbefore = obj['rtbefore']
                rank = obj['rank']
                sql = """INSERT INTO tweet_in_session(is_favorited_before,session_id,tweet_id,has_retweet_before,tweet_seen,tweet_retweeted,tweet_favorited,rank)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s);"""
                conn_cur.execute(sql,(fav_before,sid,tid,rtbefore,tweet_seen,retweet_now,favorite_now,rank,))
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
    sql = """INSERT INTO truman_user(assignment_id,twitter_id,Hit_id,exp_condition)
         VALUES(%s,%s,%s,%s) RETURNING worker_id;"""
    try:
        connection = accessPool.getconn()
        if connection is not False: 
            twitter_id = request.args.get('twitter_id')
            hit_id = request.args.get('screen_name')
            cursor = connection.cursor()
            cursor.execute(sql, ("BETA",twitter_id,hit_id,"EXP_COND",))
            retVal123 = cursor.fetchall()[0][0]
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
            return jsonify(data=retVal123)
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)
    return retVal123

@app.route('/insert_session', methods=['GET']) # Also must return session ID. We might want the date also..
def insert_session():
    retVal123 = -1
    try:
        #Getting connection from pool
        connection = accessPool.getconn()
        if connection is not False:
            now_session_start = datetime.datetime.now()
            session_start = str(now_session_start.year) + '-' + str(now_session_start.month) + '-' + str(now_session_start.day) + ' ' + str(now_session_start.hour) + ':' + str(now_session_start.minute) + ':' + str(now_session_start.second)
            worker_id = request.args.get('worker_id')
            sql = """INSERT INTO session(session_start,session_end,worker_id)
                VALUES(%s,%s,%s) RETURNING session_id;"""
            cursor = connection.cursor()
            cursor.execute(sql,(session_start,session_start,worker_id,))
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

@app.route('/insert_click', methods=['POST'])
def insert_click(): # This will take many arguments and takes logic in the guest access twitter to work
    connection = None
    try:
        #Getting connection from pool
        connection = accessPool.getconn()
        if connection is not False:
            timestamp = datetime.datetime.now()
            timestamp_str = str(timestamp.year) + '-' + str(timestamp.month) + '-' + str(timestamp.day) + ' ' + str(timestamp.hour) + ':' + str(timestamp.minute) + ':' + str(timestamp.second)
            tweet_id = request.args.get('tweet_id')
            session_id = request.args.get('session_id')
            urll = request.args.get('urll')
            iscard = request.args.get('iscard')
            sql = """INSERT INTO click(tweet_id,url,is_card,click_timestamp,session_id)
            VALUES(%s,%s,%s,%s,%s);"""
            cursor = connection.cursor()
            cursor.execute(sql,(tweet_id,urll,iscard,timestamp_str,session_id,)) # could pass False directly maybe? not sure if it will translate right
            #returnData = cursor.fetchall()
            cursor.close()
            connection.commit()
            accessPool.putconn(connection) #closing the connection
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/insert_tracking', methods=['POST'])
def insert_tracking():
    connection = None
    try:
        connection = accessPool.getconn()
        if connection is not False:
            session_id = request.args.get('session_id')
            furthestSeen = int(request.args.get('furthestSeen'))
            sql = """UPDATE tweet_in_session SET tweet_seen = %s WHERE session_id = %s and rank = %s"""
            cursor = connection.cursor()
            for rank_seen in range(1,furthestSeen+1):
                cursor.execute(sql,(str(True),session_id,rank_seen,))
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
    except Exception as error:
        print(error)
    return "Done!"

@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    #await queueLoop()
    app.run(host = "127.0.0.1", port = 5052)