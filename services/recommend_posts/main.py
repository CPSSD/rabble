#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import os
import time

from utils.connect import get_service_channel
from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import PostRecommendationsServicer

from services.proto import database_pb2_grpc
from services.proto import recommend_posts_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser(
        'Run the Rabble recommend_posts microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def main():
    args = get_args()
    logger = get_logger('recommend_posts_service', args.v)
    logger.info('Creating recommend_posts server')

    with get_service_channel(logger, "DB_SERVICE_HOST", 1798) as db_chan:
        db_stub = database_pb2_grpc.DatabaseStub(db_chan)
        users_util = UsersUtil(logger, db_stub)

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        servicer = PostRecommendationsServicer(users_util, logger, db_stub)
        recommend_posts_pb2_grpc.add_PostRecommendationsServicer_to_server(servicer,
                                                                           server)

        server.add_insecure_port('0.0.0.0:1814')
        logger.info("Starting recommend_posts service on port 1814")
        server.start()
        try:
            while True:
                time.sleep(60 * 60 * 24)  # One day
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
