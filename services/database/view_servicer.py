import sqlite3

from services.proto import database_pb2 as db_pb


class ViewDatabaseServicer:
    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._logger.debug("View database servicer")

    def AddView(self, req, context):
        self._logger.debug(
            "Adding view by %d to path %s",
            req.user, req.path
        )
        response = db_pb.AddViewResponse()
        # TODO: insert datetime too
        try:
            pass
            '''
            self._db.execute(
                'INSERT INTO views (user_id, path) '
                'VALUES (?, ?)',
                req.user,
                req.path,
                commit=True
            )'''
        except sqlite3.Error as e:
            #self._db.commit()
            self._logger.error("AddView error: %s", str(e))
        return response


