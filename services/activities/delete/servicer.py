from services.proto import delete_pb2_grpc

from send_delete_servicer import SendLikeDeleteServicer
from receive_delete_servicer import ReceiveLikeDeleteServicer


class S2SDeleteServicer(delete_pb2_grpc.S2SDeleteServicer):
    def __init__(self, logger, db, activ_util, users_util):
        send_like_delete = SendLikeDeleteServicer(
            logger, db, activ_util, users_util)
        self.SendLikeDeleteActivity = send_like_delete.SendLikeDeleteActivity
        rd = ReceiveLikeDeleteServicer(logger, db, activ_util, users_util)
        self.ReceiveLikeDeleteActivity = rd.ReceiveLikeDeleteActivity

