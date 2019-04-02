from services.proto import update_pb2_grpc

from send_update_servicer import SendUpdateServicer
from receive_update_servicer import ReceiveUpdateServicer


class S2SUpdateServicer(update_pb2_grpc.S2SUpdateServicer):
    def __init__(self, logger, db, activ_util, users_util):
        send_update = SendUpdateServicer(
            logger, db, activ_util, users_util)
        self.SendUpdateActivity = send_update.SendUpdateActivity
        rd = ReceiveUpdateServicer(logger, db, activ_util, users_util)
        self.ReceiveUpdateActivity = rd.ReceiveUpdateActivity

