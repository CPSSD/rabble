import sqlite3

from services.proto import database_pb2 as db_pb


class LikeDatabaseServicer:
    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

    def LikesCollection(self, req, context):
        self._logger.debug(
            "Got likes collection request for article %d",
            req.article_id
        )
        response = db_pb.LikesCollectionResponse(
            result_type=db_pb.LikesCollectionResponse.OK,
        )
        try:
            res = self._db.execute(
                "SELECT user_id FROM likes "
                "WHERE article_id = ?",
                req.article_id)
            response.liking_user_ids.extend(
                [u[0] for u in res])
        except sqlite3.Error as e:
            self._logger.error("LikesCollection error: %s", str(e))
            response.result_type = db_pb.LikesCollectionResponse.ERROR
            response.error = str(e)
        return response

    def LikedCollection(self, req, context):
        self._logger.debug(
            "Got liked collection request for user %d",
            req.user_id
        )
        response = db_pb.LikedCollectionResponse(
            result_type=db_pb.LikedCollectionResponse.OK,
        )
        try:
            res = self._db.execute(
                "SELECT posts.ap_id FROM posts "
                "INNER JOIN likes ON likes.article_id = posts.global_id "
                "WHERE likes.user_id = ?"
                "ORDER BY posts.global_id DESC",
                req.user_id)
            response.liked_ap_ids.extend(
                [p[0] for p in res])
        except sqlite3.Error as e:
            self._logger.error("LikedCollection error: %s", str(e))
            response.result_type = db_pb.LikedCollectionResponse.ERROR
            response.error = str(e)
        return response

    def AddLike(self, req, context):
        self._logger.debug(
            "Adding like by %d to article %d",
            req.user_id, req.article_id
        )
        response = db_pb.DBLikeResponse(
            result_type=db_pb.DBLikeResponse.OK
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
            self._db.discard_cursor()
            self._logger.error("AddLike error: %s", str(e))
            response.result_type = db_pb.DBLikeResponse.ERROR
            response.error = str(e)
        return response

    def RemoveLike(self, req, context):
        self._logger.debug(
            "Removing like by %d to article %d",
            req.user_id, req.article_id)
        response = db_pb.DBLikeResponse(
            result_type=db_pb.DBLikeResponse.OK
        )
        try:
            self._db.execute(
                'DELETE FROM likes WHERE user_id=? AND article_id=?',
                req.user_id, req.article_id, commit=False)
            self._db.execute(
                'UPDATE posts SET likes_count = likes_count - 1 '
                'WHERE global_id=?',
                req.article_id,
                commit=True
            )
        except sqlite3.Error as e:
            self._db.discard_cursor()
            self._logger.error("RemoveLike error %s", str(e))
            response.result_type = db_ob.DBLikeResponse.ERROR
            response.error = str(e)
        return response

