from services.proto import undo_pb2_grpc

from send_undo_servicer import SendLikeUndoServicer
from receive_undo_servicer import ReceiveLikeUndoServicer


class S2SUndoServicer(undo_pb2_grpc.S2SUndoServicer):
    def __init__(self, logger, db, activ_util, users_util):
        send_like_undo = SendLikeUndoServicer(
            logger, db, activ_util, users_util)
        self.SendLikeUndoActivity = send_like_undo.SendLikeUndoActivity
        rd = ReceiveLikeUndoServicer(logger, db, activ_util, users_util)
        self.ReceiveLikeUndoActivity = rd.ReceiveLikeUndoActivity

