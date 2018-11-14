from proto import users_pb2
from proto import database_pb2

class LoginHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub

    def Login(self, request, context):
        pass

