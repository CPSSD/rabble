from services.proto import delete_pb2_grpc

from send_delete_servicer import SendDeleteServicer
from receive_delete_servicer import ReceiveDeleteServicer


class S2SDeleteServicer(delete_pb2_grpc.S2SDeleteServicer):
    def __init__(self, logger, db, activ_util):
        self._logger = logger
        self._receive_delete = ReceiveDeleteServicer(
            logger, db, activ_util)
        self._send_delete = SendDeleteServicer(
            logger, db, activ_util)

    def SendDeleteActivity(self, req, ctx):
        return self._send_delete.SendDeleteActivity(req, ctx)

    def ReceiveDeleteActivity(self, req, ctx):
        return self._receive_delete.ReceiveDeleteActivity(req, ctx)

