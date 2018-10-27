import follows_pb2


class SendFollowServicer:

    def __init__(self, logger):
        self._logger = logger

    def SendFollowRequest(self, request, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info('Send  follow request.')
        resp.result_type = follows_pb2.FollowResponse.OK
        return response
