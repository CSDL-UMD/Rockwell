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
params = config()
accessPool =  psycopg2.pool.SimpleConnectionPool(MIN, MAX,host="early-database-truman.c8wc9kfclicm.us-east-2.rds.amazonaws.com",database="metrics",user="platform_manager",password="xZw53AbD",port="5432")# Maybe make 2 pools and half the functions use each or make this one huge.
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
async def queueLoop() -> None: # async so it doesnt interfere with the rest of the execution.
            """ Hold a queue of overflow and squeeze them in as the program runs """
            # Main loop of the dequeue function
            while True: # Runs throughout program to flush queue.
                while len(universal_buffer) > 0:
                    try:
                        info = universal_buffer.pop(0) # Get the first in line (put in function call) Deleteing with pop, if write fails it will be added here again through the function itself.
                        if info.at(0) == "insert_tweet":
                            status = insert_tweet(info.at(1))
                        elif info.at(0) == "insert_tweet_session":
                            status = insert_tweet_session(info.at(1),info.at(2),info.at(3),info.at(4),info.at(5))
                        # elif ....
                        if status == "Full":
                            time.sleep(1)
                    except FullQueue:
                        time.sleep(1) # wait one second when the queue has data but connections are full.
            time.sleep(5)


@app.route('/insert_tweet', methods=['POST'])
def insert_tweet():
    try:
        #Getting connection from pool
        tweet_id = int(request.args.get('tweet_id'))
        connection = None
        try: 
            connection = accessPool.getconn()
        except:
            print("NO CONNECTION")
            connection = False
        if connection is not False:
            sql = """INSERT INTO tweet(tweet_id) VALUES(%s) ON CONFLICT DO NOTHING;"""
            try:
                conn_cur = connection.cursor()
                conn_cur.execute(sql, (tweet_id,))
                #returnData = conn_cur.fetchall()
                #conn_cur.commit()
                conn_cur.close()
                connection.commit()
                accessPool.putconn(connection) #closing the connection
            except Exception as error:# (Exception, psycopg2.DatabaseError) as error:
                print("ERROR!!!!",error)
        else:
            data = []
            data.append("insert_tweet")
            data.append(tweet_id)
            universal_buffer.append(data) # offload it to the queue.
            #return "Full"
    except Exception as error:
        print(error)
    return "Done!"

@app.route('/insert_tweet_session', methods=['POST'])
def insert_tweet_session(): # This will take many arguments and takes logic in the guest access twitter to work
    favorite_now = False
    retweet_now = False
    tweet_seen = False
    connection = None
    try:
        #Getting connection from pool
        connection = accessPool.getconn()
        if connection is not False:
            fav_before = request.args.get('fav_before')
            sid = request.args.get('sid')
            tid = request.args.get('tid')
            rtbefore = request.args.get('rtbefore')
            rank = request.args.get('rank')
            sql = """INSERT INTO tweet_in_session(is_favorited_before,session_id,tweet_id,has_retweet_before,tweet_seen,tweet_retweeted,tweet_favorited,rank)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s);"""
            cursor = connection.cursor()
            cursor.execute(sql,(fav_before,sid,tid,rtbefore,tweet_seen,retweet_now,favorite_now,rank,)) # could pass False directly maybe? not sure if it will translate right
            #returnData = cursor.fetchall()
            cursor.close()
            connection.commit()
            accessPool.putconn(connection) #closing the connection
        else:   #Indicates the pool is full
            print("Coming here")
            data = []
            data.append("insert_tweet_session")
            data.append(fav_before)
            data.append(sid)
            data.append(tid)
            data.append(rtbefore)
            data.append(rank)
            universal_buffer.append(data) # offload it to the queue.
            #return "Full"
    except Exception as error:
        print(error)
    return "Done!"

def insert_user(self,worker_id,assignment_id,twitter_id,hit_id,exp_condition) -> None:
        """ insert a new vendor into the vendors table """
        sql = """INSERT INTO truman_user(worker_id,assignment_id,twitter_id,Hit_id,exp_condition)
             VALUES(%s,%s,%s,%s,%s) RETURNING worker_id;"""
        try:
            connection = accessPool.getconn()
            if connection is not False: 
                cursor = connection.cursot()
                cursor.execute(sql, (worker_id,assignment_id,twitter_id,hit_id,exp_condition,))
                cursor.close()
                connection.commit()
                accessPool.putconn(connection)
        except (Exception, psycopg2.DatabaseError) as error:
            print("ERROR!!!!",error)

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
            twitter_id = request.args.get('twitter_id')
            sql = """INSERT INTO session(session_start,session_end,twitter_id,worker_id)
                VALUES(%s,%s,%s,%s) RETURNING session_id;"""
            cursor = connection.cursor()
            cursor.execute(sql,(session_start,session_start,twitter_id,worker_id,))
            retVal123 = cursor.fetchall()[0][0]
            cursor.close()
            connection.commit()
            accessPool.putconn(connection)
            return jsonify(data=retVal123)
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)
    return retVal123


@app.route('/insert_user_tweet_ass', methods=['POST'])
def insert_usert_tweet():
    try:
        #Getting connection from pool
        connection = accessPool.getconn()
        if connection is not False:
            now = datetime.datetime.now()
            time = now.year + '-' + now.month + '-' + now.day + ' ' + now.hour + ':' + now.minute + ':' + now.second
            worker_id = request.args.get('worker_id')
            tweet_id = reqest.args.get('tweet_id')
            sql = """INSERT INTO user_tweet_ass(tweet_id,worker_id,)
                VALUES(%s,%s) RETURNING session_id;"""
            cursor = connection.cursor()
            cursor.execute(sql,(tweet_id,worker_id,))
            cursor.close()
            accessPool.putconn(connection)
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)


@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    #await queueLoop()
    app.run(host = "127.0.0.1", port = 5052)