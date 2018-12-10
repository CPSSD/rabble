#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import os
import sys
import time

from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import ActorsServicer

from services.proto import database_pb2_grpc
from services.proto import actors_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser(
        'Run the Rabble actors microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_database_service_address(logger):
    host = os.environ.get('DB_SERVICE_HOST')
    if not host:
        logger.error('DB_SERVICE_HOST env var not set.')
        sys.exit(1)
    addr = host + ':1798'
    return addr


def main():
    args = get_args()
    logger = get_logger('actors_service', args.v)
    logger.info('Creating server')

    db_addr = get_database_service_address(logger)

    with grpc.insecure_channel(db_addr) as db_chan:
        db_stub = database_pb2_grpc.DatabaseStub(db_chan)

        users_util = UsersUtil(logger, db_stub)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        servicer = ActorsServicer(logger, users_util, db_stub)
        actors_pb2_grpc.add_ActorsServicer_to_server(servicer,
                                                     server)

        server.add_insecure_port('0.0.0.0:1973')
        logger.info('Starting server')
        server.start()
        try:
            while True:
                time.sleep(60 * 60 * 24)  # One day
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
