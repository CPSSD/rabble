from services.proto import announce_pb2_grpc

from send_announce_servicer import SendAnnounceServicer
from receive_announce_servicer import ReceiveAnnounceServicer


class AnnounceServicer(announce_pb2_grpc.AnnounceServicer):
    def __init__(self, logger, db, user_util, activ_util, article_stub):
        self._logger = logger
        send_announce_servicer = SendAnnounceServicer(
            logger, db, user_util, activ_util)
        self.SendAnnounceActivity = send_announce_servicer.SendAnnounceActivity

        receive_announce_servicer = ReceiveAnnounceServicer(
            logger, db, user_util, activ_util, article_stub)
        self.ReceiveAnnounceActivity = receive_announce_servicer.ReceiveAnnounceActivity
