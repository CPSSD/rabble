#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from utils.connect import get_service_channel, get_future_channel
from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import CreateServicer
from services.proto import create_pb2_grpc
from services.proto import database_pb2_grpc
from services.proto import article_pb2_grpc
from utils.activities import ActivitiesUtil


def get_args():
    parser = argparse.ArgumentParser('Run the rabble create microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()

def main():
    args = get_args()
    logger = get_logger("create_service", args.v)

    db_channel = get_service_channel(logger, "DB_SERVICE_HOST", 1798)
    db_stub = database_pb2_grpc.DatabaseStub(db_channel)
    article_channel = get_future_channel(logger, "ARTICLE_SERVICE_HOST", 1601)
    article_stub = article_pb2_grpc.ArticleStub(article_channel)
    logger.info("Creating create server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_util = UsersUtil(logger, db_stub)
    activ_util = ActivitiesUtil(logger)
    create_pb2_grpc.add_CreateServicer_to_server(
        CreateServicer(db_stub, article_stub, logger, users_util, activ_util),
        server
        )
    server.add_insecure_port('0.0.0.0:1922')
    logger.info("Starting create server on port 1922")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        db_channel.close()
        pass

if __name__ == '__main__':
    main()
