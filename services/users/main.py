#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import os
import sys
import time

from utils.connect import get_service_channel
from utils.logger import get_logger
from users_servicer import UsersServicer
from services.proto import users_pb2_grpc
from services.proto import database_pb2_grpc


def get_db_stub(logger):
    chan = get_service_channel(logger, "DB_SERVICE_HOST", 1798)
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
    users_pb2_grpc.add_UsersServicer_to_server(
        UsersServicer(logger, get_db_stub(logger)),
        server)
    server.add_insecure_port('0.0.0.0:1534')
    logger.info("Starting users server at port 1534")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
