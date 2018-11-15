import bcrypt

from proto import users_pb2
from proto import database_pb2

class CreateHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'),
                             bcrypt.gensalt())

    def Create(self, request, context):
        insert_request = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.INSERT,
            entry=database_pb2.UsersEntry(
                handle=request.handle,
                display_name=request.display_name,
                password=self._hash_password(request.password),
                bio=request.bio,
            ),
        )
        db_resp = self._db_stub.Users(insert_request)
        if db_resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.warning("Error inserting user into db: %s",
                                 db_resp.error)
            return users_pb2.CreateResponse(
                result_type=users_pb2.CreateResponse.ERROR,
                error_details=db_resp.error,
            )
        return users_pb2.CreateResponse(
            result_type=users_pb2.CreateResponse.OK,
        )


