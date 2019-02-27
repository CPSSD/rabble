from services.proto import delete_pb2_grpc

from send_delete_servicer import SendLikeDeleteServicer
from receive_delete_servicer import ReceiveDeleteServicer


class S2SDeleteServicer(delete_pb2_grpc.S2SDeleteServicer):
    def __init__(self, logger, db, activ_util):
        send_like_delete = SendLikeDeleteServicer(logger, db, activ_util)
        self.SendLikeDeleteActivity = send_like_delete.SendLikeDeleteActivity
        receive_delete = ReceiveDeleteServicer(logger, db, activ_util)
        self.ReceiveDeleteActivity = receive_delete.ReceiveDeleteActivity

