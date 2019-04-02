#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from services.proto import database_pb2_grpc
from services.proto import update_pb2_grpc
from utils.activities import ActivitiesUtil
from utils.connect import get_service_channel
from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import S2SUpdateServicer


def get_args():
    parser = argparse.ArgumentParser('Run the update activity microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_db_stub(logger):
    chan = get_service_channel(logger, "DB_SERVICE_HOST", 1798)
    return database_pb2_grpc.DatabaseStub(chan)


def main():
    args = get_args()
    logger = get_logger("update_service", args.v)
    db_stub = get_db_stub(logger)
    activ_util = ActivitiesUtil(logger, db_stub)
    users_util = UsersUtil(logger, db_stub)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    update_pb2_grpc.add_S2SUpdateServicer_to_server(
        S2SUpdateServicer(logger, db_stub, activ_util, users_util),
        server
    )
    server.add_insecure_port("0.0.0.0:2029")
    logger.info("Starting Update service on port 2029")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
