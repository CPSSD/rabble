#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import CreateServicer
from proto import create_pb2_grpc
from proto import database_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the rabble create microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_db_channel():
    db_service_host = os.environ.get("DB_SERVICE_HOST")
    if not db_service_host:
        print("Please set DB_SERVICE_HOST env variable")
        sys.exit(1)
    db_service_address = db_service_host + ":1798"
    return grpc.insecure_channel(db_service_address)


def main():
    args = get_args()
    logger = get_logger("create_service", args.v)
    logger.info("Creating db connection")
    db_channel = get_db_channel()
    db_stub = database_pb2_grpc.DatabaseStub(db_channel)
    logger.info("Creating create server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    users_util = UsersUtil(logger, db_stub)
    create_pb2_grpc.add_CreateServicer_to_server(
        CreateServicer(db_stub, logger, users_util),
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
