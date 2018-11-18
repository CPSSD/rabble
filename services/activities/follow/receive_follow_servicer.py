import json

from proto import follows_pb2
from proto import follows_pb2_grpc
from proto import s2s_follow_pb2

class ReceiveFollowServicer:

    def __init__(self, logger, users_util, follows_service):
        self._logger = logger
        self._users_util = users_util
        self._follows_stub = follows_service

    def _s2s_req_to_follows_req(self, req):
        a = follows_pb2.ForeignToLocalFollow()
        _, a.followed = self._users_util.parse_actor(req.followed)
        a.follower_host, a.follower_handle = \
            self._users_util.parse_actor(req.follower)
        return a

    def ReceiveFollowActivity(self, req, context):
        self._logger.info('Received follow activity: {}'.format(req))
        resp = s2s_follow_pb2.FollowActivityResponse()
        resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK

        follow = self._s2s_req_to_follows_req(req)
        follows_resp = self._follows_stub.ReceiveFollowRequest(follow)

        resp.result_type = follows_resp.result_type
        resp.error = follows_resp.error
        return resp
