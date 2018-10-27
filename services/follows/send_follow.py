import follows_pb2


class SendFollowServicer:

    def __init__(self, logger, database_stub):
        self._logger = logger
        self._database_stub = database_stub

    def SendFollowRequest(self, request, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info('Send follow request.')

        print(request.follower)
        print(request.followed)
        follow = database_pb2.LocalFollow()
        self._database_stub.Follows(follow)
        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
