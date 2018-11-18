from send_follow_servicer import SendFollowServicer
from receive_follow_servicer import ReceiveFollowServicer
from proto import s2s_follow_pb2_grpc


class FollowServicer(s2s_follow_pb2_grpc.S2SFollowServicer):

    def __init__(self, logger, users_util, follows_service_address):
        self._logger = logger
        self._users_util = users_util
        self._follows_service_address = follows_service_address

        send_follow_servicer = SendFollowServicer(logger)
        self.SendFollowActivity = send_follow_servicer.SendFollowActivity
        receive_follow_servicer = ReceiveFollowServicer(logger, users_util,
                                                        follows_service_address)
        self.ReceiveFollowActivity = receive_follow_servicer.ReceiveFollowActivity
