from services.proto import delete_pb2_grpc

from send_delete_servicer import SendLikeDeleteServicer
from receive_delete_servicer import ReceiveDeleteServicer


class S2SDeleteServicer(delete_pb2_grpc.S2SDeleteServicer):
    def __init__(self, logger, db, activ_util):
        self._logger = logger
        self._receive_delete = ReceiveDeleteServicer(
            logger, db, activ_util)
        self._send_like_delete = SendLikeDeleteServicer(
            logger, db, activ_util)

    def SendLikeDeleteActivity(self, req, ctx):
        return self._send_like_delete.SendLikeDeleteActivity(req, ctx)

    def ReceiveDeleteActivity(self, req, ctx):
        return self._receive_delete.ReceiveDeleteActivity(req, ctx)

