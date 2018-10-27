#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import logging
import time

from servicer import ArticleServicer
import article_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the rabble article microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_logger(level):
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(level)
    return logger


def main():
    args = get_args()
    logger = get_logger(args.v)
    logger.info("Creating article server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    article_pb2_grpc.add_ArticleServicer_to_server(
        ArticleServicer(logger),
        server
        )
    server.add_insecure_port('0.0.0.0:1601')
    logger.info("Starting server on port 1601")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
