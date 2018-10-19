import sqlite3

import database_pb2
import database_pb2_grpc

class DatabaseServicer(database_pb2_grpc.DatabaseServicer):
    def __init__(self, db):
        self._db = db
        self._type_handlers = {
            database_pb2.PostsRequest.INSERT: self._handle_insert,
            database_pb2.PostsRequest.FIND: self._handle_find,
            database_pb2.PostsRequest.DELETE: self._handle_delete,
            database_pb2.PostsRequest.UPDATE: self._handle_update,
        }

    def Posts(self, request, context):
        response = database_pb2.PostsResponse()
        self._type_handlers[request.request_type](request, response)
        return response

    def _handle_insert(self, req, resp):
        try:
            self._db.execute(
                'INSERT INTO posts '
                '(global_id, author, title, body, creation_datetime) '
                'VALUES (?, ?, ?, ?, ?)',
                req.entry.global_id, req.entry.author,
                req.entry.title, req.entry.body,
                req.entry.creation_datetime.seconds)
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.PostsResponse.OK

    def _handle_find(self, req, resp):
        pass

    def _handle_delete(self, req, resp):
        pass

    def _handle_update(self, req, resp):
        pass
