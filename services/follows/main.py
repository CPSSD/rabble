#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import os
import sys
import time

from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import FollowsServicer
from util import Util

from services.proto import database_pb2_grpc
from services.proto import follows_pb2_grpc
from services.proto import s2s_follow_pb2_grpc
from services.proto import rss_pb2_grpc
from services.proto import approver_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the Rabble following microservice')
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


def get_follow_activity_service_address(logger):
    host = os.environ.get('FOLLOW_ACTIVITY_SERVICE_HOST')
    if not host:
        logger.error('FOLLOW_ACTIVITY_SERVICE_HOST env var not set.')
        sys.exit(1)
    addr = host + ':1922'
    return addr

def get_approver_service_address(logger):
    host = os.environ.get('APPROVER_SERVICE_HOST')
    if not host:
        logger.error('APPROVER_SERVICE_HOST env var not set.')
        sys.exit(1)
    addr = host + ':2077'
    return addr

def get_rss_service_address(logger):
    host = os.environ.get('RSS_SERVICE_HOST')
    if not host:
        logger.error('RSS_SERVICE_HOST env var not set.')
        sys.exit(1)
    addr = host + ':1973'
    return addr


def main():
    args = get_args()
    logger = get_logger('follows_service', args.v)
    logger.info('Creating server')

    db_addr = get_database_service_address(logger)
    follow_addr = get_follow_activity_service_address(logger)
    approver_addr = get_approver_service_address(logger)
    rss_addr = get_rss_service_address(logger)

    with grpc.insecure_channel(db_addr) as db_chan, \
         grpc.insecure_channel(follow_addr) as follow_chan, \
         grpc.insecure_channel(approver_addr) as approver_chan, \
         grpc.insecure_channel(rss_addr) as rss_chan:

        db_stub = database_pb2_grpc.DatabaseStub(db_chan)
        rss_stub = rss_pb2_grpc.RSSStub(rss_chan)
        follow_stub = s2s_follow_pb2_grpc.S2SFollowStub(follow_chan)
        approver_stub = approver_pb2_grpc.ApproverStub(approver_chan)

        util = Util(logger, db_stub, approver_stub)
        users_util = UsersUtil(logger, db_stub)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        follows_servicer = FollowsServicer(logger, util, users_util, db_stub,
                                           follow_stub, approver_stub, rss_stub)
        follows_pb2_grpc.add_FollowsServicer_to_server(follows_servicer,
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
