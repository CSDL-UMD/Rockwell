import time
import heapq
import schedule
import random

# users = {'1': [time.time() + 100, 1, [11, 12, 13, 14], 0], '2': [time.time(), 0, [21, 22, 23, 24], 0], '3': [time.time(), 0, [31, 32, 33, 34], 0], '4': [time.time(), 0, [41, 42, 43, 44], 0]}
# users is a dictionary in the form user_id: [reset_time, number_of_retweets_in_time_window, all_pending_requests, number_of_likes_in_time_window]
users = {}
requests = [('1', 'like', 1)]
# this is the shared user dictionary for retweets
limit = 2  # this is the current implemented limit


class Producer:
    def __init__(self):
        self.pq = []

    def push(self, user_id: str, request_id: int, reset_time: float, request_type: str, request) -> None:
        """
            this is the only function that is allowed to push to the queue
            the priotiry is calculated using the diff between the reset time and now
            and id is saved for futher sorting and other data for consumer use
        """
        now = time.time() - 10  # the real one will be just the current time
        heapq.heappush(self.pq, (int(reset_time - now), request_id, reset_time, user_id, request, request_type))

    def update(self, requests):
        """
            this function updates the queue with the requests that failed to be processed
            Args:
                requests: this is the list of request that are ready to be processed regarless of rate limit
        """
        for ele in requests:
            user_id = ele[3]
            request = ele[4]
            request_type = ele[5]
            user = users[user_id]
            reset_time = user[0]
            id = user[2].index(request)
            user[1] = 0
            self.push(user_id, id, reset_time, request_type, request)

    def get_ready_requests(self):
        """
            This function is used to get all the requests from the queue that are ready to go right now.
            It does it by continuisly popping from the queue until the queue is empty or until the element popped out is not ready to be processed
            Returns:
                a list of ready requests 
        """
        now = time.time()
        ready = []  # collecting the requests here

        while True and len(self.pq):
            item = heapq.heappop(self.pq)  # get the item off the queue
            if item[2] <= now:  # check if the item is ready to go
                ready.append(item) 
            else:  
                heapq.heappush(self.pq, item)
                break
        return ready


class Consumer:
    """
        this the consumer class to consume the requests
    """


    def wake_up(self):
        lst = producer.get_ready_requests()
        if len(lst):
            rest = self.consume(lst)
            producer.update(rest)
        else:
            print('nothing ready')

    def consume(self, requests):
        """
            the consumer takes the requests and takes care of the requests that are ready to be 
            processed until the limit and returns the ones that are left.

            Args:
                requests: list of requests to be processed

            Returns:
                unprocessed requests
        """

        rest = []

        for ele in requests:
            user_id = ele[3]
            user = users[user_id]
            count = 0
            if ele[5] == 'like':
                count = user[3]
            if count < limit:
                reset_time = process(ele)
                user[1] += 1
                user[0] = reset_time
                user[2].pop(0)
            else:
                rest.append(ele)
        return rest


def process(request):
    print(request)
    return time.time()


# if it wakes up often and nothing happens maybe sleep for a while and wait for new push
# remove if block and run the code when the module is imported
# same producer and consumer between likes and retweets
producer = Producer()
consumer = Consumer()



def make_request(request_type: str, request, user_id: str) -> None:
    print('same thing')
    request_id = 0
    if user_id in users:
        request_id = len(users[user_id][3])
        users[user_id][3].append(request)
        
    else:
        users[user_id] = [time.time(), 0, [request], 0]
    
    producer.push(user_id,request_id, time.time(), request_type, request)

def make_requests() -> None:
    print("here")
    for ele in requests:
        user_id = ele[0]
        request_type = ele[1]
        request = ele[2]
        
        request_id = 0
        if user_id in users:
            request_id = len(users[user_id][2])
            users[user_id][2].append(request)
        
        else:
            users[user_id] = [time.time(), 0, [request], 0]
    
        producer.push(user_id,request_id, time.time(), request_type, request)

    requests = []

schedule.every(2).seconds.do(consumer.wake_up)
schedule.every(1).seconds.do(make_requests)
while True:
    schedule.run_pending()
    time.sleep(1)

