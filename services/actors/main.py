#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import os
import sys
import time

from utils.connect import get_service_channel
from utils.logger import get_logger
from utils.users import UsersUtil
from utils.activities import ActivitiesUtil
from servicer import Servicer

from services.proto import database_pb2_grpc
from services.proto import follows_pb2_grpc
from services.proto import actors_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser(
        'Run the Rabble actors microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()

def get_host_name(logger):
    host = os.environ.get('HOST_NAME')
    if not host:
        logger.error('HOST_NAME env var not set.')
        sys.exit(1)
    return host


def main():
    args = get_args()
    logger = get_logger('actors_service', args.v)
    logger.info('Creating server')

    with get_service_channel(logger, "DB_SERVICE_HOST", 1798) as db_chan, \
         get_service_channel(logger, "FOLLOWS_SERVICE_HOST", 1641) as follows_chan:
        db_stub = database_pb2_grpc.DatabaseStub(db_chan)
        follows_stub = follows_pb2_grpc.FollowsStub(follows_chan)

        users_util = UsersUtil(logger, db_stub)
        activities_util = ActivitiesUtil(logger)
        host_name = get_host_name(logger)

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        servicer = Servicer(logger, users_util, activities_util,
                                  db_stub, host_name, follows_stub)
        actors_pb2_grpc.add_ActorsServicer_to_server(servicer, server)

        server.add_insecure_port('0.0.0.0:1973')
        logger.info("Starting actors service on port 1973")
        server.start()
        try:
            while True:
                time.sleep(60 * 60 * 24)  # One day
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
