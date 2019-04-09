#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from services.proto import database_pb2_grpc
from services.proto import like_pb2_grpc
from services.proto import recommend_posts_pb2_grpc
from utils.activities import ActivitiesUtil
from utils.connect import get_service_channel
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
    chan = get_service_channel(logger, "DB_SERVICE_HOST", 1798)
    return database_pb2_grpc.DatabaseStub(chan)


def get_post_recommendation_stub(logger):
    post_recommender_location = os.environ.get("POST_RECOMMENDATIONS_NO_OP")
    if not post_recommender_location:
        logger.error(
            "Environment variable POST_RECOMMENDATIONS_NO_OP not set.")
        return None
    if post_recommender_location != "./services/noop":
        chan = get_service_channel(
            logger, "POST_RECOMMENDATIONS_SERVICE_HOST", 1814)
        return recommend_posts_pb2_grpc.PostRecommendationsStub(chan)
    logger.info("Recommender service is NO-OP.")
    return None


def main():
    args = get_args()
    logger = get_logger("likes_service", args.v)
    db_stub = get_db_stub(logger)
    post_recommendation_stub = get_post_recommendation_stub(logger)
    user_util = UsersUtil(logger, db_stub)
    activ_util = ActivitiesUtil(logger, db_stub)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    like_pb2_grpc.add_S2SLikeServicer_to_server(
        S2SLikeServicer(logger, db_stub, user_util,
                        activ_util, post_recommendation_stub),
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
