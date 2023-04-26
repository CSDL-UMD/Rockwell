""" Cron job for pulling data from home timelines """

import requests as rq
import os
import glob
import gzip
import json
import logging
from itertools import groupby
from datetime import datetime
from argparse import ArgumentParser

HOST_DEFAULT="127.0.0.1"
PORT_DEFAULT=5054
LOG_FMT_DEFAULT='%(asctime)s:%(levelname)s:%(message)s'
LOG_PATH_DEFAULT="./cronjob.log"


def make_logger(path=LOG_PATH_DEFAULT):
    """ 
    By default, log to file messages at level INFO or above. By default, the
    log file will be located in same location from where the script is being
    called. It also adds a stream handler for logging to the console messages
    at level ERROR and above; these will be logged to stderr.
    """
    logging.basicConfig(filename=path,
                        format=LOG_FMT_DEFAULT,
                        filemode='a',
                        level="INFO")
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter(LOG_FMT_DEFAULT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def make_parser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", help="directory with data files")
    parser.add_argument("collection_days", help="Number of days for collection")
    parser.add_argument("-H", "--host", 
                        help=f"eligibility API host (default: {HOST_DEFAULT})")
    parser.add_argument("-p", "--port", 
                        help=f"eligibiility API port (default: {PORT_DEFAULT})")
    parser.add_argument("-l", "--log", metavar="PATH",
                        help=f"log all errors to PATH (default: {LOG_PATH_DEFAULT})")
    parser.set_defaults(host=HOST_DEFAULT, 
                        port=PORT_DEFAULT, 
                        log=LOG_PATH_DEFAULT)
    return parser


def main(data_dir, collection_days, host=HOST_DEFAULT, port=PORT_DEFAULT, log_path=LOG_PATH_DEFAULT):
    time_now = datetime.now()
    logger = make_logger(log_path)
    data_dir = os.path.abspath(data_dir)
    logging.info(f"Cron job started: {data_dir=}, {host=}, {port=}")
    os.chdir(data_dir)
    home_timeline_files = sorted(glob.glob("*_home_*.json.gz"))
    files_by_user = groupby(home_timeline_files, key=lambda k: k.split("_")[0])
    for user, user_files in files_by_user:
        logging.info(f"Collecting data for {user=}")
        latest_user_file = max(user_files, key=lambda fn: int(fn.split(".")[0].split("_")[2]))
        path = os.path.join(data_dir, latest_user_file)
        with gzip.open(path, 'r') as fin:
            try:
                data = json.loads(fin.read().decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON data: {path}", exc_info=e)
                continue
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
            worker_id = data["worker_id"]
            since_id = data['latestTweetId']
            initial_time = data['collectionStarted']
            data_error_msg = data['errorMessage']
            time_diff_days = 0
            inital_time_datetime = datetime.strptime(initial_time, '%Y-%m-%dT%H:%M:%S')
            time_diff = (time_now - inital_time_datetime).total_seconds()
            time_diff_days = time_diff/86400
            new_file_number = int(latest_user_file.split(".")[0].split("_")[2]) + 1
        except KeyError as e:
            logger.error(f"Problem getting fields for {user=}", exc_info=e)
            continue
        if "Invalid Token" in data_error_msg:
            # Skip users who revoked access
            logger.warning(f"Ignoring user who revoked access: user {user} "\
                            f"MturkId {mturk_id} "\
                            f"MturkHitId {mturk_hit_id} "\
                            f"MturkAssignmentId {mturk_assignment_id}")
            continue
        if time_diff_days > int(collection_days):
            # Skip users whose data was collected for the predefined collection days
            logger.warning(f"Ignoring user whose data collection is completed: user {user} "\
                            f"MturkId {mturk_id} "\
                            f"MturkHitId {mturk_hit_id} "\
                            f"MturkAssignmentId {mturk_assignment_id}")
            continue
        try:
            url_path = f"/hometimeline?worker_id={worker_id}"\
                f"&max_id={since_id}"\
                f"&collection_started={initial_time}"\
                f"&file_number={new_file_number}"
            res = rq.get(f"http://{host}:{port}{url_path}")
            if res.ok:
                out = res.json()
                if out['errorMessage'].strip() != "NA":
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
    main(args.data_dir, args.collection_days, args.host, args.port, args.log)