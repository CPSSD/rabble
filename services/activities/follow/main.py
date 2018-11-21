#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from utils.logger import get_logger
from utils.users import UsersUtil

from servicer import FollowServicer
from services.proto import follows_pb2_grpc
from services.proto import s2s_follow_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the follow activity microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_follows_service_address(logger):
    host = os.environ.get('FOLLOWS_SERVICE_HOST')
    if not host:
        logger.error('FOLLOWS_SERVICE_HOST env var not set.')
        sys.exit(1)
    addr = host + ':1641'
    return addr


def main():
    args = get_args()
    logger = get_logger("s2s_follow_service", args.v)
    users_util = UsersUtil(logger, None)
    with grpc.insecure_channel(get_follows_service_address(logger)) as chan:
        follows_service = follows_pb2_grpc.FollowsStub(chan)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        s2s_follow_pb2_grpc.add_S2SFollowServicer_to_server(
            FollowServicer(logger, users_util, follows_service),
            server
        )
        server.add_insecure_port('0.0.0.0:1922')
        logger.info("Starting s2s follow server on port 1922")
        server.start()
        while True:
            time.sleep(60 * 60 * 24)  # One day

if __name__ == '__main__':
    main()
