import sqlite3

from services.proto import database_pb2 as db_pb


class LikeDatabaseServicer:
    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

    def AddLike(self, req, context):
        self._logger.debug(
            "Adding like by %d to article %d",
            req.user_id, req.article_id
        )
        response = db_pb.AddLikeResponse(
            result_type=db_pb.AddLikeResponse.OK
        )
        try:
            self._db.execute(
                'INSERT INTO likes (user_id, article_id) '
                'VALUES (?, ?)',
                req.user_id,
                req.article_id,
                commit=False
            )
            self._db.execute(
                'UPDATE posts SET likes_count = likes_count + 1 '
                'WHERE global_id=?',
                req.article_id
            )
        except sqlite3.Error as e:
            self._logger.error("AddLike error: %s", str(e))
            response.result_type = db_pb.AddLikeResponse.ERROR
            response.error = str(e)
        return response


