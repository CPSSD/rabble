#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time
import os
import sys

from utils.logger import get_logger
from servicer import FollowServicer 
from proto import s2s_follow_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the follow activity microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def main():
    args = get_args()
    logger = get_logger("s2s_follow_service", args.v)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    s2s_follow_pb2_grpc.add_S2SFollowServicer_to_server(
        FollowServicer(logger),
        server
    )
    server.add_insecure_port('0.0.0.0:1922')
    logger.info("Starting s2s follow server on port 1922")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        db_channel.close()
        pass

if __name__ == '__main__':
    main()
