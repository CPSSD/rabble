#!/usr/bin/env python3
from concurrent import futures

import argparse
import grpc
import time
import os
import sys

from utils.activities import ActivitiesUtil
from utils.logger import get_logger
from utils.users import UsersUtil
from servicer import ApproverServicer
from services.proto import database_pb2_grpc
from services.proto import approver_pb2_grpc

def get_args():
    parser = argparse.ArgumentParser('Run the rabble approval microservice')
    parser.add_argument(
        '-v', default='WARNING', action='store_const', const='DEBUG',
        help='Log more verbosely.')
    return parser.parse_args()

def get_db_channel_address(logger):
    db_service_host = os.environ.get("DB_SERVICE_HOST")
    if not db_service_host:
        logger.error("Please set DB_SERVICE_HOST env variable")
        sys.exit(1)
    return db_service_host + ":1798"

def main():
    args = get_args()
    logger = get_logger("create_service", args.v)
    activ_util = ActivitiesUtil(logger)

    logger.info("Creating db connection")

    with grpc.insecure_channel(get_db_channel_address(logger)) as db_chan:
        db_stub = database_pb2_grpc.DatabaseStub(db_chan)

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        approver_pb2_grpc.add_ApproverServicer_to_server(
            ApproverServicer(logger, db_stub, activ_util),
            server,
        )
        
        server.add_insecure_port('0.0.0.0:2077')
        logger.info("Starting approver service on port 2077")
        server.start()
        while True:
            time.sleep(60 * 60 * 24)  # One day
        

if __name__ == '__main__':
    main()
