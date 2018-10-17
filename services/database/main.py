#!/usr/bin/env python3
from concurrent import futures
import argparse
import grpc
import time

from database import build_database
from servicer import DatabaseServicer
import database_pb2_grpc

def get_args():
    parser = argparse.ArgumentParser('Run the Rabble database microservice')
    parser.add_argument('db_schema', help='The path to the init script')
    return parser.parse_args()

def main():
    args = get_args()
    print("Creating DB")
    database = build_database(args.db_schema)
    print("Creating server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    print("Creating database servicer")
    database_pb2_grpc.add_DatabaseServicer_to_server(
            DatabaseServicer(database), server)
    server.add_insecure_port('0.0.0.0:1798')
    print("Starting server")
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
