from proto import users_pb2_grpc

class UsersServicer(users_pb2_grpc.UsersServicer):
    def __init__(self, logger):
        self._logger = logger

    def Login(self, request, context):
        pass

    def Create(self, request, context):
        pass

