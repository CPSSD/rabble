from google.protobuf.timestamp_pb2 import Timestamp
import sqlite3

import database_pb2
import database_pb2_grpc


class UsersDatabaseServicer(database_pb2_grpc.DatabaseServicer):

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._users_type_handlers = {
            database_pb2.UsersRequest.INSERT: self._users_handle_insert,
        }

    def Users(self, request, context):
        response = database_pb2.UsersResponse()
        self._users_type_handlers[request.request_type](request, response)
        return response

    def _users_handle_insert(self, req, resp):
        self._logger.info('Inserting new user into Users database.')
        try:
            self._db.execute(
                'INSERT INTO users '
                '(handle, display_name) '
                'VALUES (?, ?)',
                req.entry.handle,
                req.entry.display_name)
        except sqlite3.Error as e:
            self._logger.error(str(e))
            resp.result_type = database_pb2.UsersResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.UsersResponse.OK
