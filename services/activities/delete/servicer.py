from services.proto import delete_pb2_grpc

from send_delete_servicer import SendDeleteServicer
from receive_delete_servicer import ReceiveDeleteServicer


class S2SDeleteServicer(delete_pb2_grpc.S2SDeleteServicer):
    def __init__(self, logger, db, activ_util, users_util):
        send_delete = SendDeleteServicer(
            logger, db, activ_util, users_util)
        self.SendDeleteActivity = send_delete.SendDeleteActivity
        rd = ReceiveDeleteServicer(logger, db, activ_util, users_util)
        self.ReceiveDeleteActivity = rd.ReceiveDeleteActivity

