from services.proto import undo_pb2_grpc

from send_delete_servicer import SendLikeDeleteServicer
from receive_delete_servicer import ReceiveLikeDeleteServicer


class S2SDeleteServicer(undo_pb2_grpc.S2SUndoServicer):
    def __init__(self, logger, db, activ_util, users_util):
        send_like_delete = SendLikeDeleteServicer(
            logger, db, activ_util, users_util)
        self.SendLikeUndoActivity = send_like_delete.SendLikeDeleteActivity
        rd = ReceiveLikeDeleteServicer(logger, db, activ_util, users_util)
        self.ReceiveLikeUndoActivity = rd.ReceiveLikeDeleteActivity

