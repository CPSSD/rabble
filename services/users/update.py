from services.proto import users_pb2
from services.proto import database_pb2

from util import get_user_and_check_pw
import bcrypt


class UpdateHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'),
                             bcrypt.gensalt())

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

        pw = None
        if request.new_password:
            pw = self._hash_password(request.new_password)

        update_request = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.UPDATE,
            match=user,
            entry=database_pb2.UsersEntry(
                display_name=request.display_name,
                password=pw,
                bio=request.bio,
                private=request.private,
                post_title_css=request.post_title_css,
                post_body_css=request.post_body_css,
            ),
        )

        db_resp = self._db_stub.Users(update_request)
        if db_resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.warning("Error update user: %s", db_resp.error)
            return users_pb2.CreateUserResponse(
                result_type=users_pb2.CreateUserResponse.ERROR,
                error=db_resp.error,
            )

        return users_pb2.UpdateUserResponse(
            result=users_pb2.UpdateUserResponse.ACCEPTED,
        )
