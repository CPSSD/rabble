#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import logging
import os
import sys
import time

from servicer import FollowsServicer
from util import Util

import database_pb2_grpc
import follows_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the Rabble following microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_logger(level):
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(level)
    return logger


def get_database_service_address():
    host = os.environ['DB_SERVICE_HOST']
    if not host:
        logger.error('DB_SERVICE_HOST env var not set.')
        sys.exit(1)
    addr = host + ':1798'
    return addr


def main():
    args = get_args()
    logger = get_logger(args.v)
    logger.info('Creating server')

    util = Util(logger)

    with grpc.insecure_channel(get_database_service_address()) as chan:
        stub = database_pb2_grpc.DatabaseStub(chan)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        follows_pb2_grpc.add_FollowsServicer_to_server(FollowsServicer(logger, util, stub),
                                                       server)

        server.add_insecure_port('0.0.0.0:1641')
        logger.info('Starting server')
        server.start()
        try:
            while True:
                time.sleep(60 * 60 * 24)  # One day
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()
