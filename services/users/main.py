#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time

from utils.logger import get_logger
from users_servicer import UsersServicer
from proto import users_pb2_grpc


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
        UsersServicer(logger), server)
    server.add_insecure_port('0.0.0.0:1798')
    logger.info("Starting users server")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
