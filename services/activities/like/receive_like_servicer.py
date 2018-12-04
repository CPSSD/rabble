from services.proto import like_pb2

class ReceiveLikeServicer:
    def __init__(self, logger):
        self._logger = logger

    def ReceiveLikeActivity(self, req, context):
        pass

