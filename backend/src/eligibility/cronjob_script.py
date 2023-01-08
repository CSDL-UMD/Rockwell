""" Cron job for pulling data from home timelines """

import requests as rq
import os
import glob
import gzip
import json
import logging
from itertools import groupby
from argparse import ArgumentParser

HOST_DEFAULT="127.0.0.1"
PORT_DEFAULT=5000
LOG_FMT_DEFAULT='%(asctime)s:%(levelname)s:%(message)s'
logging.basicConfig(filename="cronjob.log",
                    format=LOG_FMT_DEFAULT,
                    filemode='a',
                    level="INFO")
logger = logging.getLogger()
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter(LOG_FMT_DEFAULT)
ch.setFormatter(formatter)
logger.addHandler(ch)

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
    data_dir = os.path.abspath(data_dir)
    logging.info(f"Cron job started: {data_dir=}, {host=}, {port=}")
    os.chdir(data_dir)
    home_timeline_files = sorted(glob.glob("*_home_*.json.gz"))
    files_by_user = groupby(home_timeline_files, key=lambda k: k.split("_")[0])
    for user, user_files in files_by_user:
        logging.info(f"Collecting data for {user=}")
        latest_user_file = max(user_files, key=lambda fn: fn.split("_")[2])
        path = os.path.join([data_dir, latest_user_file])
        with gzip.open(path, 'r') as fin:
            try:
                data = json.loads(fin.read().decode('utf-8'))
            except UnicodeError as e:
                logger.error(f"Error decoding UTF-8 data: {path}", exc_info=e)
                continue
            except IOError as e:
                logger.error(f"I/O error reading data: {path} ", exc_info=e)
                continue
        try:
            access_token = data['accessToken']
            access_token_secret = data['accessTokenSecret']
            mturk_id = data['MTurkId']
            mturk_hit_id = data['MTurkHitId']
            mturk_assignment_id = data['MTurkAssignmentId']
            since_id = data['latestTweetId']
            data_error = data.get('ResponseObject', {})['error']
            data_error_msg = data.get('ResponseObject', {})['errorMessage']
        except KeyError as e:
            logger.error(f"Problem getting fields for {user=}", exc_info=e)
            continue
        if data_error and "Error while authenticating" in data_error_msg:
            # Skip users who revoked access
            logger.warning(f"Ignoring user who revoked access: user {user} "\
                            f"MturkId {mturk_id} "\
                            f"MturkHitId {mturk_hit_id} "\
                            f"MturkAssignmentId {mturk_assignment_id}")
            continue
        try:
            url_path = f"/api/hometimeline/{access_token}"\
                f"&{access_token_secret}"\
                f"&{mturk_id}"\
                f"&{mturk_hit_id}"\
                f"&{mturk_assignment_id}"\
                f"&{since_id}"
            res = rq.get(f"http://{host}:{port}{url_path}")
            if res.ok:
                out = res.json()
                if out['error']:
                    errorMessage = out['errorMessage']
                    logger.error(f"Error from Twitter API: user {user} "\
                                   f"MturkId {mturk_id} "\
                                   f"MturkHitId {mturk_hit_id} "\
                                   f"MturkAssignmentId {mturk_assignment_id}:"\
                                   f"{errorMessage}")
            else:
                logger.error(f"Eligibility response failed with "\
                               f"status {res.status_code}: user {user}")
        except Exception as e:
            logger.error(f"Problem in requesting eligibility API: "\
                         f" user {user}", exc_info=e)
    logger.info("Cron job ended.")


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    main(args.data_dir, args.host, args.port)
