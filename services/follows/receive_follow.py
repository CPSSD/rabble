import follows_pb2


class ReceiveFollowServicer:

    def __init__(self, logger, database_stub):
        self._logger = logger
        self._database_stub = database_stub

    def ReceiveFollowRequest(self, request, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info('Receive follow request.')
        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
