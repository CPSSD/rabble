from services.proto import users_pb2_grpc
from login import LoginHandler
from create import CreateHandler


class UsersServicer(users_pb2_grpc.UsersServicer):
    def __init__(self, logger, db_stub):
        self._login = LoginHandler(logger, db_stub)
        self._create = CreateHandler(logger, db_stub)

    def Login(self, request, context):
        return self._login.Login(request, context)

    def Create(self, request, context):
        return self._create.Create(request, context)

