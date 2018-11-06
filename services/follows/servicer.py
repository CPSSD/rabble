from get_followers import GetFollowsReceiver
from receive_follow import ReceiveFollowServicer
from send_follow import SendFollowServicer

from proto import follows_pb2_grpc


class FollowsServicer(follows_pb2_grpc.FollowsServicer):

    def __init__(self, logger, util, users_util, database_stub):
        self._logger = logger
        self._util = util
        self._users_util = users_util

        send_servicer = SendFollowServicer(logger, util, users_util,
                                           database_stub)
        self.SendFollowRequest = send_servicer.SendFollowRequest
        rec_servicer = ReceiveFollowServicer(logger, util, users_util,
                                             database_stub)
        self.ReceiveFollowRequest = rec_servicer.ReceiveFollowRequest

        get_follows_receiver = GetFollowsReceiver(logger, util, users_util,
                                                  database_stub)
        self.GetFollowers = get_follows_receiver.GetFollowers
        self.GetFollowing = get_follows_receiver.GetFollowing
