from receive_follow import ReceiveFollowServicer
from send_follow import SendFollowServicer

import follows_pb2_grpc


class FollowsServicer(follows_pb2_grpc.FollowsServicer):

    def __init__(self, logger):
        self._logger = logger

        send_servicer = SendFollowServicer(logger)
        self.SendFollowRequest = send_servicer.SendFollowRequest
        rec_servicer = ReceiveFollowServicer(logger)
        self.ReceiveFollowRequest = rec_servicer.ReceiveFollowRequest
