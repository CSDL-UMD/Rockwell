import time
import heapq
import schedule
import threading
import logging
from configparser import ConfigParser
from requests_oauthlib import OAuth1Session
from datetime import datetime

log_level = logging.DEBUG
logging.basicConfig(filename='ratelimiter.log', level=log_level)

# users is a dictionary in the form user_id: [reset_time, number_of_retweets_in_time_window, number_of_likes_in_time_window, oauth]
users = {}
# this is the shared user dictionary for retweets
limit = 6  # this is the current implemented limit

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

class Producer:
    def __init__(self):
        self.pq = []
        self.counter = 0

    def push(self, user_id: str, request_type: str, tweet_id, users: dict = users, request_id: int = 0) -> None:
        """
            this is the only function that is allowed to push to the queue
            the priotiry is calculated using the diff between the reset time and now
            and id is saved for futher sorting and other data for consumer use
        """
        # print('producer push')
        # reset_time = 0
        # if user_id in users:
        #    reset_time = users[user_id][0]
        # else:
        #    users[user_id] = [time.time(), 0, 0, None]


        if request_type == 'retweet':
            reset_time = users[user_id][3]

        else:
            reset_time = users[user_id][4]
        
        logging.info(f'pushing a {request_type} from {user_id} at {datetime.now()}')
        if request_id == 0:
            request_id = self.counter
            self.counter += 1

        heapq.heappush(self.pq, (reset_time, request_id, user_id, tweet_id, request_type))

    def update(self, requests) -> None:
        """
            this function updates the queue with the requests that failed to be processed
            Args:
                requests: this is the list of request that are ready to be processed regarless of rate limit
        """
        # print('updating')
        # print('^^^^^^^^^^^', requests)
        logging.info('Updating priority queue')
        for ele in requests:
            user_id = ele[2]
            request = ele[3]
            request_type = ele[4]
            user = users[user_id]
            if request_type == 'retweet':
                user[1] = 5
            elif request_type == 'like':
                user[2] = 5
            else:
                logging.error(f"request type is not a like or retweet but instead {request_type}")
            self.push(user_id, request_type, request, request_id=ele[1])

        # print('after update', self.pq)
        # pq gets updated to some value that is the implement, the ids did not disapear they just spawned back where they did not need to be
    def get_ready_requests(self) -> list:
        """
            This function is used to get all the requests from the queue that are ready to go right now.
            It does it by continuisly popping from the queue until the queue is empty or until the element popped out is not ready to be processed
            Returns:
                a list of ready requests
        """
        now = time.time()
        ready = []  # collecting the requests here
        
        logging.info('Getting all ready requests')

        while True and len(self.pq):
            item = heapq.heappop(self.pq)  # get the item off the queue
            if item[0] <= now:  # check if the item is ready to go
                ready.append(item)
            else:
                heapq.heappush(self.pq, item)
                break
        return ready


class Consumer:
    """
        this the consumer class to consume the requests
    """

    def wake_up(self, producer):
        lst = producer.get_ready_requests()
        if len(lst):
            rest = self.consume(lst, users)

            if len(rest):
                producer.update(rest)
        else:
            print('nothing ready')

    def consume(self, requests, users):
        """
            the consumer takes the requests and takes care of the requests that are ready to be
            processed until the limit and returns the ones that are left.

            Args:
                requests: list of requests to be processed

            Returns:
                unprocessed requests
        """

        rest = []
        # print('consuming from ratelimiter')
        # print('**********************',requests, '******************************')
        for ele in requests:
            user_id = ele[2]
            user = users[user_id]
            if ele[4] == 'like' and user[2] > 0:
                # if user has an oauth use it else oauth them
                is_rate_limit = process(ele)
                if is_rate_limit:
                    rest.append(ele)
                # user[2] += 1 # counter like requests in the window
                # user[0] = reset_time # reset time
            elif ele[4] == 'retweet' and user[1] > 0:
                is_rate_limit = process(ele)
                if is_rate_limit:
                    rest.append(ele)
                # user[1] += 1 # counter of retweets requests in the window
                # user[0] = reset_time
            else:
                rest.append(ele)
        # print('++++++', rest, '++++++')
        return rest

# use the logging module to document the process see cardinfo.py in feed generation
def process(request):
    user_id = request[2]
    tweet_id = request[3]
    request_type = request[4]
    oauth = users[user_id][0]
    payload = {"tweet_id" : tweet_id}
    successfull = False
    rate_limit = False
    response = None
    if request_type == 'retweet':
        response = oauth.post("https://api.twitter.com/2/users/{}/retweets".format(user_id), json=payload)
        if 'data' in response.json().keys():
            if 'retweeted' in response.json()['data'].keys():
                if response.json()['data']['retweeted']:
                    users[user_id][1] = int(response.headers['x-rate-limit-remaining'])
                    users[user_id][3] = response.headers['x-rate-limit-reset']
                    successfull = True
        elif 'status' in response.json().keys():
            if response.json()['status'] == 429:
                users[user_id][1] = int(response.headers['x-rate-limit-remaining'])
                users[user_id][3] = response.headers['x-rate-limit-reset']
                rate_limit = True
    else:
        response = oauth.post("https://api.twitter.com/2/users/{}/likes".format(user_id), json=payload)
        if 'data' in response.json().keys():
            if 'liked' in response.json()['data'].keys():
                if response.json()['data']['liked']:
                    users[user_id][2] = int(response.headers['x-rate-limit-remaining'])
                    users[user_id][4] = response.headers['x-rate-limit-reset']
                    successfull = True
        elif 'status' in response.json().keys():
            if response.json()['status'] == 429:
                users[user_id][2] = int(response.headers['x-rate-limit-remaining'])
                users[user_id][4] = response.headers['x-rate-limit-reset']
                rate_limit = True
    if rate_limit:
        return True
    if not successfull:
        response_text = response.text
        logging.info(f"EXCEPTION MANUAL CHECK : {user_id=} {tweet_id=} {request_type=} {response_text=}")
    return False

    # print('processing')
    # print(request)
    # return time.time()


# if it wakes up often and nothing happens maybe sleep for a while and wait for new push
# remove if block and run the code when the module is imported
# same producer and consumer between likes and retweets
producer = Producer()
consumer = Consumer()


def push_like(tweet_id, user_id, access_token, access_token_secret) -> None:
    """
        when the user likes a post this function is used to send the like request to a producer class that takes care of the rest

        Args:
        tweet_id: is the id of the tweeet that was liked
        user_id: is the id of the user that liked the post
    """
    if user_id not in users.keys():
        cred = config('../configuration/config.ini','twitterapp')
        cred['token'] = access_token.strip()
        cred['token_secret'] = access_token_secret.strip()
        oauth = OAuth1Session(cred['key'],
                            client_secret=cred['key_secret'],
                            resource_owner_key=cred['token'],
                            resource_owner_secret=cred['token_secret'])
        users[user_id] = [oauth, 5, 5, time.time(), time.time()]
    producer.push(user_id, 'like', tweet_id)


def push_retweet(tweet_id, user_id, access_token, access_token_secret) -> None:
    """
        when the user retweets a post this function is used to send the retweet request to a producer class that takes care of thr rest

        Args:
        tweet_id: is the id the tweet that was retweeted
        user_id: is the id of the user performing the action
    """
    if user_id not in users.keys():
        cred = config('../configuration/config.ini', 'twitterapp')
        cred['token'] = access_token.strip()
        cred['token_secret'] = access_token_secret.strip()
        oauth = OAuth1Session(cred['key'],
                            client_secret=cred['key_secret'],
                            resource_owner_key=cred['token'],
                            resource_owner_secret=cred['token_secret'])
        users[user_id] = [oauth, 5, 5, time.time(), time.time()]
    producer.push(user_id, 'retweet', tweet_id)


schedule.every(2).seconds.do(consumer.wake_up, producer)


def main():
    while True:
        schedule.run_pending()
        time.sleep(1)


thread_2 = threading.Thread(target=main)
thread_2.start()
