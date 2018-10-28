#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import logging
import time

from logger_servicer import LoggerServicer
import logger_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the Rabble logger microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    parser.add_argument('-f', default='rabble.log',
        help='The file to write logs to')
    return parser.parse_args()


def get_local_logger(level):
    logger = logging.getLogger(__name__ + '_local')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(level)
    return logger


def get_file_logger(filename):
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.FileHandler(filename))
    logger.setLevel(logging.DEBUG)
    return logger


def main():
    args = get_args()
    logger = get_file_logger(args.f)
    local_logger = get_local_logger(args.v)
    local_logger.info("Creating server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    local_logger.info("Creating logger servicer")
    logger_pb2_grpc.add_LoggerServicer_to_server(
        LoggerServicer(logger), server)
    server.add_insecure_port('0.0.0.0:1867')
    local_logger.info("Starting server")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
