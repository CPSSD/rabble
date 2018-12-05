from services.proto import like_pb2

class ReceiveLikeServicer:
    def __init__(self, logger):
        self._logger = logger

    def ReceiveLikeActivity(self, req, context):
        return like_pb2.LikeResponse(
            result_type=like_pb2.LikeResponse.ERROR,
            error="Not implemented",
        )

