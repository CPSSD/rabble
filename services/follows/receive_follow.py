import follows_pb2


class ReceiveFollowServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

    def ReceiveFollowRequest(self, request, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info('Receive follow request.')
        resp.result_type = database_pb2.FollowResponse.OK
        return response
