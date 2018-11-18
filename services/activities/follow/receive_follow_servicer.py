import json

from proto import follows_pb2
from proto import follows_pb2_grpc
from proto import s2s_follow_pb2

class ReceiveFollowServicer:

    def __init__(self, logger, users_util, follows_service_address):
        self._logger = logger
        self._users_util = users_util
        self._follows_service_address = follows_service_address
        self.__follows_stub = None

    def _get_follows_stub(self):
        if self.__follows_stub is not None:
            return self.__follows_stub
        chan = grpc.insecure_channel(self._follows_service_address)
        self.__follows_stub = follows_pb2_grpc.FollowsStub(chan)
        return self.__follows_stub

    def _s2s_req_to_follows_req(req):
        a = follows_pb2.ForeignToLocalFollow()
        a.followed, _ = self._users_util.parse_username(req.followed)
        a.follower_handle, a.follower_host = \
            self._users_util.parse_username(req.follower)
        return a

    def ReceiveFollowActivity(self, req, context):
        resp = s2s_follow_pb2.FollowActivityResponse()
        resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK

        follow = self._s2s_req_to_follows_req(req)
        stub = self._get_follows_stub()
        follows_resp = stub.ReceiveFollowRequest(follow)

        resp.result_type = follows_resp.result_type
        resp.error = follows_resp.error
        return resp
