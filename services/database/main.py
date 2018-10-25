#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import logging
import time

from database import build_database
from servicer import DatabaseServicer
import database_pb2_grpc


def get_args():
    parser = argparse.ArgumentParser('Run the Rabble database microservice')
    parser.add_argument(
        '--schema', required=True,
        help='The path to the schema script for the database.')
    parser.add_argument(
        '--db_path', default='rabble.db',
        help='The path to the sqlite database file')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()


def get_logger(level):
    # TODO(CianLR): Move to shared package and add ability to send to
    # centralised logging service.
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(level)
    return logger


def main():
    args = get_args()
    logger = get_logger(args.v)
    logger.info("Creating DB")
    database = build_database(logger, args.schema, args.db_path)
    logger.info("Creating server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logger.info("Creating database servicer")
    database_pb2_grpc.add_DatabaseServicer_to_server(
        DatabaseServicer(database, logger), server)
    server.add_insecure_port('0.0.0.0:1798')
    logger.info("Starting server")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
