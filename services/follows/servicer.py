from get_followers import GetFollowersReceiver
from receive_follow import ReceiveFollowServicer
from send_follow import SendFollowServicer

import follows_pb2_grpc


class FollowsServicer(follows_pb2_grpc.FollowsServicer):

    def __init__(self, logger, util, database_stub):
        self._logger = logger
        self._util = util

        send_servicer = SendFollowServicer(logger, util, database_stub)
        self.SendFollowRequest = send_servicer.SendFollowRequest
        rec_servicer = ReceiveFollowServicer(logger, util, database_stub)
        self.ReceiveFollowRequest = rec_servicer.ReceiveFollowRequest

        get_follows_receiver = GetFollowsReceiver(logger, util, database_stub)
        self.GetFollowers = get_follows_receiver.GetFollowers
        self.GetFollowing = get_follows_receiver.GetFollowing
