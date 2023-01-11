import requests as rq
import time
import os

def current_milli_time():
    return round(time.time() * 1000)

endpoints = ["hometimeline", "usertimeline", "favorites"]

host = "127.0.0.1"
port = 6000

# placeholder values
mturk_id = 123
mturk_hit_id = 456
mturk_assignment_id = 789

# get access token and access token secret from environment
try:
    access_token = os.environ['KEY']
    access_token_secret = os.environ['KEY_SECRET']
except KeyError as e:
    print(f"Error: no {e.args[0]} found in the environment. Please export it.")
    import sys
    sys.exit(1)

# URL format is:
#
# /api/:endpoint/:access_token&:access_token_secret&:mturk_id&:mturk_hit_id&:mturk_assignment_id

total_time = 0
for endpoint in endpoints:
    url_path = f"/api/{endpoint}/{access_token}&{access_token_secret}" \
        "&{mturk_id}&{mturk_hit_id}&{mturk_assignment_id}"
    print(f"Querying {endpoint}...")
    start = current_milli_time()
    res = rq.get(f"http://{host}:{port}{url_path}")
    end = current_milli_time()
    if res.ok:
        out = res.json()
        if not out['error']:
            print(out)
            print("Elapsed time: " + str(end - start))
        else:
            #print("API0I Rate-Limit reached")
            print(res)
            print(out)
    else:
        print(f"Error: response failed with status: {res.status_code}")
    print()
    total_time += (end - start)
print(f"Total elapsed time: {total_time}")