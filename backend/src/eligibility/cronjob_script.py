import requests as rq
import os
import glob
import gzip
import json
import logging
from datetime import datetime

host = "127.0.0.1"
port = 5000

logging.basicConfig(filename="cronjob.log",
                    format='%(asctime)s %(message)s',
                    filemode='a')

logger = logging.getLogger()

data_dir = "/home/saumya/Documents/USF/Project/ASD/mock_social_media_platform/infodiversity-mock-social-media/backend/src/eligibility/User_Data/"
os.chdir(data_dir)

home_timeline_files = []
for fn in glob.glob("*_home_*.json.gz"):
    home_timeline_files.append(fn)

users = [file.split('_')[0] for file in home_timeline_files]
users = list(set(users))

for user in users:
    try:
        times = []
        user_files = []
        for file in home_timeline_files:
            if file.split('_')[0] == user and file.split('_')[1] == 'home':
                time_str = file.split('_')[2].split('.')[0]
                times.append(datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S'))
                user_files.append(file)
        latest_time = max(times)
        latest_user_file = user_files[times.index(latest_time)]
    except Exception as e:
        logger.warning(f"Problem in getting the latest file : User {user} : Exception {str(e)}")
        continue
    with gzip.open(data_dir + latest_user_file, 'r') as fin:
        data = json.loads(fin.read().decode('utf-8'))
    try:
        access_token = data['accessToken']
        access_token_secret = data['accessTokenSecret']
        mturk_id = data['MTurkId']
        mturk_hit_id = data['MTurkHitId']
        mturk_assignment_id = data['MTurkAssignmentId']
        since_id = data['latestTweetId']
        data_error = data['ResponseObject']['error']
        data_error_msg = data['ResponseObject']['errorMessage']
        if data_error:
            if "Error while authenticating" in data_error_msg:
                logger.warning(f"Ignoring the data for user who revoked access : User {user} MturkId {mturk_id} MturkHitId {mturk_hit_id} MturkAssignmentId {mturk_assignment_id}")
                continue
    except Exception as e:
        logger.warning(f"Problem in getting fields from the latest file : User {user} : Exception {str(e)}")
        continue
    try:
        url_path = f"/api/hometimeline/{access_token}&{access_token_secret}&{mturk_id}&{mturk_hit_id}&{mturk_assignment_id}&{since_id}"
        res = rq.get(f"http://{host}:{port}{url_path}")
        if res.ok:
            out = res.json()
            if out['error']:
                if "Error while authenticating" in out['errorMessage']:
                    logger.warning(f"Revoked access : User {user} MturkId {mturk_id} MturkHitId {mturk_hit_id} MturkAssignmentId {mturk_assignment_id}")
                else:
                    logger.warning(f"Other error in getting latest data : User {user} MturkId {mturk_id} MturkHitId {mturk_hit_id} MturkAssignmentId {mturk_assignment_id}")
        else:
            logger.warning(f"Eligibility response failed with status {res.status_code} : User {user}")
    except Exception as e:
        logger.warning(f"Problem in requesting eligibility API : User {user} : Exception {str(e)}")