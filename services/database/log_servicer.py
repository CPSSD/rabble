import sqlite3

from services.proto import database_pb2 as db_pb


class LogDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

    def AddLog(self, req, context):
        self._logger.debug(
            "Adding log '%s' by user %d",
            req.message.strip(), req.user
        )
        response = db_pb.AddLogResponse()
        try:
            self._db.execute(
                'INSERT INTO logs (user_id, message, datetime) '
                'VALUES (?, ?, ?)',
                req.user,
                req.message,
                req.datetime.seconds
            )
        except sqlite3.Error as e:
            self._logger.error("AddLog error: %s", str(e))
        return response
