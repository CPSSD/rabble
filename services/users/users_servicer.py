from proto import users_pb2_grpc
from login import LoginHandler
from create import CreateHandler
from check_token import CheckTokenHandler


class UsersServicer(users_pb2_grpc.UsersServicer):
    def __init__(self, logger, db_stub):
        self._login = LoginHandler(logger, db_stub)
        self._create = CreateHandler(logger, db_stub)
        self._check_token = CheckTokenHandler(logger, db_stub)

    def Login(self, request, context):
        return self._login.Login(request, context)

    def Create(self, request, context):
        return self._create.Create(request, context)

    def CheckToken(self, request, context):
        return self._check_token.CheckToken(request, context)

