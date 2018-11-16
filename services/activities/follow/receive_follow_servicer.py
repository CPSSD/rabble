import json

from proto import s2s_follow_pb2


class ReceiveFollowServicer:

    def __init__(self, logger):
        self._logger = logger

    def ReceiveFollowActivity(self, req, context):
        resp = s2s_follow_pb2.FollowActivityResponse()
        resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK
        return resp
