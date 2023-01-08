""" Cron job for pulling data from home timelines """

import requests as rq
import os
import glob
import gzip
import json
import logging
from datetime import datetime
from argparse import ArgumentParser

HOST_DEFAULT="127.0.0.1"
PORT_DEFAULT=5000

logging.basicConfig(filename="cronjob.log",
                    format='%(asctime)s %(message)s',
                    filemode='a')
logger = logging.getLogger()

def make_parser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", help="directory with data files")
    parser.add_argument("-H", "--host", 
                        help=f"eligibility API host (default: {HOST_DEFAULT})")
    parser.add_argument("-p", "--port", 
                        help=f"eligibiility API port (default: {PORT_DEFAULT})")
    parser.set_defaults(host=HOST_DEFAULT, port=PORT_DEFAULT)
    return parser


def main(data_dir, host=HOST_DEFAULT, port=PORT_DEFAULT):
    os.chdir(data_dir)
    home_timeline_files = glob.glob("*_home_*.json.gz")

    users = {f.split('_')[0] for f in home_timeline_files}

    for user in users:
        try:
            times = []
            user_files = []
            for fn in home_timeline_files:
                if fn.split('_')[0] == user and fn.split('_')[1] == 'home':
                    time_str = fn.split('_')[2].split('.')[0]
                    times.append(datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S'))
                    user_files.append(fn)
            latest_time = max(times)
            latest_user_file = user_files[times.index(latest_time)]
        except Exception as e:
            logger.error(f"Problem in getting the latest file: User {user}: "\
                         f"Exception {str(e)}")
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
                    logger.error(f"Ignoring user who revoked access: User {user} "\
                                 f"MturkId {mturk_id} "\
                                 f"MturkHitId {mturk_hit_id} "\
                                 f"MturkAssignmentId {mturk_assignment_id}")
                    continue
        except Exception as e:
            logger.warning(f"Problem in getting fields from the latest file: User"\
                           f"{user}: Exception {str(e)}")
            continue
        try:
            url_path = f"/api/hometimeline/{access_token}&{access_token_secret}"\
                f"&{mturk_id}&{mturk_hit_id}&{mturk_assignment_id}&{since_id}"
            res = rq.get(f"http://{host}:{port}{url_path}")
            if res.ok:
                out = res.json()
                if out['error']:
                    if "Error while authenticating" in out['errorMessage']:
                        logger.error(f"Revoked access: User {user} "\
                                     f"MturkId {mturk_id} "\
                                     f"MturkHitId {mturk_hit_id} "
                                     f"MturkAssignmentId {mturk_assignment_id}")
                    else:
                        logger.error(f"Other error in getting latest data: "\
                                     f"User {user} "\
                                     f"MturkId {mturk_id} "\
                                     f"MturkHitId {mturk_hit_id} "\
                                     f"MturkAssignmentId {mturk_assignment_id}")
            else:
                logger.error(f"Eligibility response failed with "\
                             f"status {res.status_code}: User {user}")
        except Exception as e:
            logger.error(f"Problem in requesting eligibility API: "\
                         f" User {user}: Exception {str(e)}")


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    main(args.data_dir, args.host, args.port)
