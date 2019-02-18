import sqlite3

from services.proto import database_pb2 as db_pb


class ViewDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

    def AddView(self, req, context):
        self._logger.debug(
            "Adding view of path '%s' by user %d",
            req.path, req.user
        )
        response = db_pb.AddViewResponse()
        try:
            self._db.execute(
                'INSERT INTO views (user_id, path, datetime) '
                'VALUES (?, ?, ?)',
                req.user,
                req.path,
                req.datetime.seconds
            )
        except sqlite3.Error as e:
            self._logger.error("AddView error: %s", str(e))
        return response
