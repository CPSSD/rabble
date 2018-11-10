#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from utils.logger import get_logger
from servicer import ArticleServicer
from proto import article_pb2_grpc
from proto import database_pb2_grpc
from proto import create_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the rabble article microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_db_channel(logger):
    db_service_host = os.environ["DB_SERVICE_HOST"]
    if not db_service_host:
        logger.error("Please set DB_SERVICE_HOST env variable")
        sys.exit(1)
    db_service_address = db_service_host + ":1798"
    return grpc.insecure_channel(db_service_address)


def get_create_channel(logger):
    create_service_host = os.environ["CREATE_SERVICE_HOST"]
    if not create_service_host:
        logger.error("Please set CREATE_SERVICE_HOST env variable")
        sys.exit(1)
    create_service_address = create_service_host + ":1922"
    return grpc.insecure_channel(create_service_address)


def main():
    args = get_args()
    logger = get_logger("article_service", args.v)
    logger.info("Creating db connection")
    db_channel = get_db_channel(logger)
    db_stub = database_pb2_grpc.DatabaseStub(db_channel)
    logger.info("Creating create connection")
    create_channel = get_create_channel(logger)
    create_stub = create_pb2_grpc.CreateStub(create_channel)
    logger.info("Creating article server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    article_pb2_grpc.add_ArticleServicer_to_server(
        ArticleServicer(create_stub, db_stub, logger),
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
