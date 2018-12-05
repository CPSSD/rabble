from services.proto import users_pb2
from services.proto import database_pb2

from util import get_user_and_check_pw

class UpdateHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub

    def Update(self, request, context):
        try:
            user, err = get_user_and_check_pw(self._logger,
                                              self._db_stub,
                                              request.handle,
                                              request.current_password)
        except ValueError as e:
                return users_pb2.UpdateUserResponse(
                    result=users_pb2.UpdateUserResponse.ERROR,
                    error=str(e),
                )

        if err != None:
            return users_pb2.UpdateUserResponse(
                result=users_pb2.UpdateUserResponse.DENIED,
            )

        # validated user, we could update now, but I haven't implemented it
        return users_pb2.UpdateUserResponse(
            result=users_pb2.UpdateUserResponse.ERROR,
            error="I'm sorry Sam, I'm afraid I can't do that."
        )
