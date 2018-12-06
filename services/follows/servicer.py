from get_followers import GetFollowsReceiver
from receive_follow import ReceiveFollowServicer
from send_follow import SendFollowServicer
from rss_follow import RssFollowServicer

from services.proto import follows_pb2_grpc


class FollowsServicer(follows_pb2_grpc.FollowsServicer):

    def __init__(self, logger, util, users_util, database_stub,
                follow_activity_stub, approver_stub, rss_stub):
        self._logger = logger
        self._util = util
        self._users_util = users_util
        self._follow_activity_stub = follow_activity_stub
        self._rss_stub = rss_stub
        self._approver_stub = approver_stub

        send_servicer = SendFollowServicer(logger, util, users_util,
                                           database_stub, follow_activity_stub)
        self.SendFollowRequest = send_servicer.SendFollowRequest
        rss_servicer = RssFollowServicer(logger, util, users_util,
                                           database_stub, rss_stub)
        self.RssFollowRequest = rss_servicer.RssFollowRequest
        rec_servicer = ReceiveFollowServicer(logger, util, users_util,
                                             database_stub, approver_stub)
        self.ReceiveFollowRequest = rec_servicer.ReceiveFollowRequest

        get_follows_receiver = GetFollowsReceiver(logger, util, users_util,
                                                  database_stub)
        self.GetFollowers = get_follows_receiver.GetFollowers
        self.GetFollowing = get_follows_receiver.GetFollowing
