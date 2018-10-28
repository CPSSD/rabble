import sqlite3

import database_pb2


class FollowDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._follow_type_handlers = {
            database_pb2.DbFollowRequest.INSERT: self._follow_handle_insert,
        }

    def Follow(self, request, context):
        response = database_pb2.DbFollowResponse()
        self._follow_type_handlers[request.request_type](request, response)
        return response

    def _follow_handle_insert(self, req, resp):
        self._logger.info('Inserting new follow into Follow database.')
        try:
            self._db.execute(
                'INSERT INTO follows '
                '(follower, followed) '
                'VALUES (?, ?)',
                req.entry.follower,
                req.entry.followed)
        except sqlite3.Error as e:
            self._logger.error(str(e))
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.DbFollowResponse.OK
