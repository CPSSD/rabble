from send_follow_servicer import SendFollowServicer
from receive_follow_servicer import ReceiveFollowServicer
from services.proto import s2s_follow_pb2_grpc


class FollowServicer(s2s_follow_pb2_grpc.S2SFollowServicer):

    def __init__(self, logger, users_util, follows_service):
        self._logger = logger
        self._users_util = users_util
        self._follows_service = follows_service

        send_follow_servicer = SendFollowServicer(logger)
        self.SendFollowActivity = send_follow_servicer.SendFollowActivity
        receive_follow_servicer = ReceiveFollowServicer(logger, users_util,
                                                        follows_service)
        self.ReceiveFollowActivity = receive_follow_servicer.ReceiveFollowActivity
