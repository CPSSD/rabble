import urllib3
import json

from proto import s2s_follow_pb2

class SendFollowServicer:

    def __init__(self, logger):
        self._logger = logger
        self._client = urllib3.PoolManager()

    def SendFollowActivity(self, req, context):
        resp = s2s_follow_pb2.FollowActivityResponse()
        resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK
        return resp
