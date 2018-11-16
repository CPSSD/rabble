import bcrypt

from proto import users_pb2
from proto import database_pb2

class LoginHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub

    def _check_password(self, pw, pw_hash):
        try:
            return bcrypt.checkpw(pw.encode('utf-8'),
                                  pw_hash.encode('utf-8'))
        except ValueError as e:
            self._logger.warning(
                "Password hash in DB '%s' caused an error: %s",
                pw_hash, str(e))
            return False # Invalid salt.

    def Login(self, request, context):
        find_request = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            match=database_pb2.UsersEntry(
                handle=request.handle,
            ),
        )
        db_resp = self._db_stub.Users(find_request)
        # Check for errors
        if db_resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.warning("Error getting user from DB: %s",
                                 db_resp.error)
            return users_pb2.LoginResponse(
                result=users_pb2.LoginResponse.ERROR,
                error=db_resp.error,
            )
        elif len(db_resp.results) != 1:
            self._logger.warning(
                "Got %d users matching handle %s, expecting 1",
                len(db_resp.results), request.handle)
            return users_pb2.LoginResponse(
                result=users_pb2.LoginResponse.ERROR,
                error="Got wrong number of users matching query",
            )
        # Check password
        if not self._check_password(request.password,
                                    db_resp.results[0].password):
            self._logger.info("ACCESS DENIED for user %s", request.handle)
            return users_pb2.LoginResponse(
                result=users_pb2.LoginResponse.DENIED,
            )
        self._logger.info("*hacker voice* I'm in (%s)", request.handle)
        return users_pb2.LoginResponse(
            result=users_pb2.LoginResponse.ACCEPTED,
        )

