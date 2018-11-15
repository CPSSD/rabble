from send_follow_servicer import SendFollowServicer
from proto import s2s_follow_pb2_grpc


class FollowServicer(s2s_follow_pb2_grpc.S2SFollowServicer):

    def __init__(self, logger):
        self._logger = logger

        send_follow_servicer = SendFollowServicer(logger)
        self.SendFollowActivity = send_follow_servicer.SendFollowActivity
