import requests as rq
import time
import os

def current_milli_time():
    return round(time.time() * 1000)

try:
    KEY = os.environ['KEY']
    KEY_SECRET = os.environ['KEY_SECRET']
except KeyError as e:
    print(f"Error: no {e.args[0]} found in the environment. Please export it.")
    import sys
    sys.exit(1)

# eligibility/:access_token&:access_token_secret&:mturk_id&:mturk_hit_id&:mturk_assignment_id

start = current_milli_time()
res = rq.get("http://127.0.0.1:6000/eligibility/" + KEY + '&' + KEY_SECRET + "&123&456&789")
end = current_milli_time()
out = res.json()
if not out['error']:
    print(out)
    print("Elapsed time: " + str(end - start))
else:
    print("API Rate-Limit reached")
