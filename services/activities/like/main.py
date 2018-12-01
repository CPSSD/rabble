#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from services.proto import database_pb2_grpc
from services.proto import like_pb2_grpc
from utils.activities import ActivitiesUtil
from utils.logger import get_logger
from utils.users import UsersUtil

from servicer import S2SLikeServicer


def get_args():
    parser = argparse.ArgumentParser('Run the like activity microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_db_stub(logger):
    db_host = os.environ.get('DB_SERVICE_HOST')
    if not db_host:
        logger.error("%s variable not set", DBVAR)
        sys.exit(1)
    db_address = db_host + ":1798"
    logger.info("Connecting to database at %s", db_address)
    chan = grpc.insecure_channel(db_address)
    return database_pb2_grpc.DatabaseStub(chan)


def main():
    args = get_args()
    logger = get_logger("likes_service", args.v)
    db_stub = get_db_stub(logger)
    user_util = UsersUtil(logger, db_stub)
    activ_util = ActivitiesUtil(logger)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    like_pb2_grpc.add_S2SLikeServicer_to_server(
        S2SLikeServicer(logger, db_stub, user_util, activ_util),
        server
    )
    server.add_insecure_port("0.0.0.0:1848")
    logger.info("Starting Like service on port 1848")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
