from send_follow_servicer import SendFollowServicer
from receive_follow_servicer import ReceiveFollowServicer
from services.proto import s2s_follow_pb2_grpc


class FollowServicer(s2s_follow_pb2_grpc.S2SFollowServicer):

    def __init__(self, logger, users_util, activ_util, follows_service, db_stub):
        self._logger = logger
        self._users_util = users_util
        self._follows_service = follows_service
        self._db = db_stub

        send_follow_servicer = SendFollowServicer(logger, activ_util, db_stub)
        self.SendFollowActivity = send_follow_servicer.SendFollowActivity
        self.SendUnfollowActivity = send_follow_servicer.SendUnfollowActivity
        receive_follow_servicer = ReceiveFollowServicer(logger, users_util,
                                                        follows_service)
        self.ReceiveFollowActivity = \
            receive_follow_servicer.ReceiveFollowActivity
        self.ReceiveUnfollowActivity = \
            receive_follow_servicer.ReceiveUnfollowActivity
