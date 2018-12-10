from services.proto import actors_pb2_grpc


class ActorsServicer(actors_pb2_grpc.ActorsServicer):

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._users_util = users_util
        self._db_stub = db_stub

    def Get(self, request, context):
        pass
