#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from utils.connect import get_service_channel
from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import ArticleServicer
from services.proto import article_pb2_grpc
from services.proto import database_pb2_grpc
from services.proto import create_pb2_grpc
from services.proto import mdc_pb2_grpc
from services.proto import search_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the rabble article microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()

def main():
    args = get_args()
    logger = get_logger("article_service", args.v)

    db_channel = get_service_channel(logger, "DB_SERVICE_HOST", 1798)
    db_stub = database_pb2_grpc.DatabaseStub(db_channel)

    create_channel = get_service_channel(logger, "CREATE_SERVICE_HOST", 1922)
    create_stub = create_pb2_grpc.CreateStub(create_channel)

    search_channel = get_service_channel(logger, "SEARCH_SERVICE_HOST", 1886)
    search_stub = search_pb2_grpc.SearchStub(search_channel)

    logger.info("Creating article server")
    mdc_channel = get_service_channel(logger, "MDC_SERVICE_HOST", 1937)
    mdc_stub = mdc_pb2_grpc.ConverterStub(mdc_channel)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_util = UsersUtil(logger, db_stub)
    article_pb2_grpc.add_ArticleServicer_to_server(
        ArticleServicer(create_stub, db_stub, mdc_stub, search_stub, logger, users_util),
        server
        )
    server.add_insecure_port('0.0.0.0:1601')
    logger.info("Starting article server on port 1601")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        db_channel.close()
        create_channel.close()
        pass

if __name__ == '__main__':
    main()
