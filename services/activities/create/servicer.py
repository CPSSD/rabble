from send_create_servicer import SendCreateServicer
from receive_create_servicer import ReceiveCreateServicer
from proto import create_pb2_grpc


class CreateServicer(create_pb2_grpc.CreateServicer):

    def __init__(self, db_stub, article_stub, logger, users_util):
        self._logger = logger
        self._db_stub = db_stub
        self._article_stub = article_stub
        self._users_util = users_util

        send_create_servicer = SendCreateServicer(db_stub, logger, users_util)
        self.SendCreate = send_create_servicer.SendCreate
        receive_create_servicer = ReceiveCreateServicer(
            db_stub, article_stub, logger, users_util
        )
        self.ReceiveCreate = receive_create_servicer.ReceiveCreate
