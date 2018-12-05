from services.proto import users_pb2

from util import get_user_and_check_pw

class LoginHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub

    def Login(self, request, context):
        try:
            user, err = get_user_and_check_pw(self._logger,
                                              self._db_stub,
                                              request.handle,
                                              request.password)
        except ValueError as e:
                return users_pb2.LoginResponse(
                    result=users_pb2.LoginResponse.ERROR,
                    error=str(e),
                )

        if err != None:
            return users_pb2.LoginResponse(
                result=users_pb2.LoginResponse.DENIED,
            )
        return users_pb2.LoginResponse(
            result=users_pb2.LoginResponse.ACCEPTED,
            display_name=user.display_name,
            global_id=user.global_id,
        )

