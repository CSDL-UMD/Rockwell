import time
from ratelimiter import *


while True:
    print('pushing')
    push_retweet('user_id', 3)
    push_like('user_id', 4)
    time.sleep(1)

