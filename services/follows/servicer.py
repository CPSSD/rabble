from receive_follow import ReceiveFollowServicer
from send_follow import SendFollowServicer

import follows_pb2_grpc


class FollowsServicer(follows_pb2_grpc.FollowsServicer):

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

        send_servicer = SendFollowServicer(db, logger)
        self.SendFollowRequest = send_servicer.SendFollowRequest
        rec_servicer = ReceiveFollowServicer(db, logger)
        self.ReceiveFollowRequest = rec_servicer.ReceiveFollowRequest
