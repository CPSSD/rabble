from services.proto import like_pb2_grpc

from send_like_servicer import SendLikeServicer
from receive_like_servicer import ReceiveLikeServicer


class S2SLikeServicer(like_pb2_grpc.S2SLikeServicer):
    def __init__(self, logger, db, user_util, activ_util):
        self._logger = logger
        self._recieve_like = ReceiveLikeServicer(logger)
        self._send_like = SendLikeServicer(
            logger, db, user_util, activ_util)

    def SendLikeActivity(self, req, ctx):
        return self._send_like.SendLikeActivity(req, ctx)

