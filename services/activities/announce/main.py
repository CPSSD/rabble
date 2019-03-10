#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from services.proto import database_pb2_grpc
from services.proto import announce_pb2_grpc
from services.proto import article_pb2_grpc
from utils.activities import ActivitiesUtil
from utils.connect import get_service_channel
from utils.logger import get_logger
from utils.users import UsersUtil

from servicer import AnnounceServicer


def get_args():
    parser = argparse.ArgumentParser('Run the announce activity microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_db_stub(logger):
    chan = get_service_channel(logger, "DB_SERVICE_HOST", 1798)
    return database_pb2_grpc.DatabaseStub(chan)


def get_article_stub(logger):
    chan = get_service_channel(logger, "ARTICLE_SERVICE_HOST", 1601)
    return article_pb2_grpc.ArticleStub(chan)


def main():
    args = get_args()
    logger = get_logger("announce_service", args.v)
    db_stub = get_db_stub(logger)
    article_stub = get_article_stub(logger)
    user_util = UsersUtil(logger, db_stub)
    activ_util = ActivitiesUtil(logger, db_stub)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    announce_pb2_grpc.add_AnnounceServicer_to_server(
        AnnounceServicer(logger, db_stub, user_util, activ_util, article_stub),
        server
    )
    server.add_insecure_port("0.0.0.0:1919")
    logger.info("Starting Announce service on port 1919")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
