from flask import Flask, render_template, request, url_for, jsonify
import Pool
import time
import asyncio

#Global pool variable:
pool_is_full = False
MIN = 5
MAX = 100
universal_buffer = []
accessPool = Pool.poolObject(MIN,MAX) # Maybe make 2 pools and half the functions use each or make this one huge.
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


@app.route('/insert_tweet/', methods=['GET','POST'])
def insert_tweet():
    try:
        #Getting connection from pool
        print("Request : ")
        print(request.args)
        tweet_id = request.args.get('tweet_id')
        connection = accessPool.get_conn()
        if connection is not False:
            sql = """INSERT INTO tweet(tweet_id) ON CONFLICT DO NOTHING
            VALUES(%s) RETURNING worker_id;"""
            conn_cur = connection.cursor()
            conn_cur.execute(sql)
            returnData = conn_cur.fetchall()
            conn_cur.close()
            accessPool.close_conn(connection) #closing the connection
        else:
            data = []
            data.append("insert_tweet")
            data.append(tweet_id)
            universal_buffer.append(data) # offload it to the queue.
            return "Full"
    except Exception as error:
        print(error)

@app.route('/insert_tweet_session/', methods=['GET'])
def insert_tweet_session(self,fav_before,sid,tid,rtbefore,rank): # This will take many arguments and takes logic in the guest access twitter to work
    favorite_now = False
    retweet_now = False
    tweet_seen = False

    try:
        #Getting connection from pool
        connection = accessPool.get_conn()
        if connection is not False:
            sql = """INSERT INTO tweet_in_session(fav_before,sid,tid,rtbefore,tweet_seen,retweet_now,favorite_now,rank)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING worker_id;"""
            cursor = connection.cursor()
            cursor.execute(sql)
            returnData = cursor.fetchall()
            cursor.close()
            accessPool.close_conn(connection) #closing the connection
        else:   #Indicates the pool is full
            data = []
            data.append("insert_tweet_session")
            data.append(fav_before)
            data.append(sid)
            data.append(tid)
            data.append(rtbefore)
            data.append(rank)
            universal_buffer.append(data) # offload it to the queue.
            return "Full"
    except Exception as error:
        print(error)



@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    #await queueLoop()
    app.run(host = "127.0.0.1", port = 5052)