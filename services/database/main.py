from concurrent import futures
import grpc
import time

from database import DB
from servicer import DatabaseServicer
import database_pb2

def main():
    database = DB()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    database_pb2.add_DatabaseServicer_to_server(
            DatabaseServicer(database), server)
    server.add_insecure_port('0.0.0.0:1798')
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)  # One day
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
