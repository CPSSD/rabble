#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import os
import sys
import time

from utils.logger import get_logger
from users_servicer import UsersServicer
from proto import users_pb2_grpc
from proto import database_pb2_grpc


def get_db_stub(logger):
    db_host = os.environ.get('DB_SERVICE_HOST')
    if not db_host:
        logger.error("%s variable not set", DBVAR)
        sys.exit(1)
    db_address = db_host + ":1798"
    logger.info("Connecting to database at %s", db_address)
    chan = grpc.insecure_channel(db_address)
    return database_pb2_grpc.DatabaseStub(chan)


def get_args():
    parser = argparse.ArgumentParser('Run the Rabble users microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def main():
    args = get_args()
    logger = get_logger("users_service", args.v)
    logger.info("Creating users server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logger.info("Creating users servicer")
    users_pb2_grpc.add_UsersServicer_to_server(
        UsersServicer(logger, get_db_stub(logger)),
        server)
    server.add_insecure_port('0.0.0.0:1534')
    logger.info("Starting users server")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
