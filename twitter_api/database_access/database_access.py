from flask import Flask, render_template, request, url_for, jsonify
import Pool


#Global pool variable:
MIN = 5
MAX = 50
accessPool = Pool.Pool(MIN,MAX)
app = Flask(__name__)

app.debug = False

@app.route('/insert_user/', methods=['GET']) # Saumya what do we do here? I need multiple functions as well.
def insert_user(worker_id,assignment_id,twitter_id,hit_id,exp_condition) -> None:
    try:
        #Getting connection from pool
        connection = accessPool.getconn()
        if(connection):
            cursor = connection.cursor()
            cursor.execute("select * from mobile") # as an example.
            accessPool.close_conn(connection) #closing the connection
    except:
        print("the connection object was not made.")
        """
        I dont think this will handle max connections well, we made need some kind of queue.
        But then we would need a function that handles the queue, waits and knows what function to call on it.
        It cannot be a simple await because then people will not be processed in the call order.
        We also need to find out what the best min and max connection is.
        """


@app.route('/insert_tweet/', methods =['GET']) # Like this?
def insert_tweet(self,tweet_id) -> None:
    print("Insertion here")
















@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

if __name__ == "__main__":
    app.run(host = "127.0.0.1", port = 5051)