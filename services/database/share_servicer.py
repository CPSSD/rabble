import sqlite3

from services.proto import database_pb2 as db_pb


DEFAULT_NUM_POSTS = 25


class ShareDatabaseServicer:
    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._select_base = (
            "SELECT "
            "p.global_id, p.author_id, p.title, p.body, "
            "p.creation_datetime, p.md_body, p.ap_id, p.likes_count, "
            "l.user_id IS NOT NULL, f.follower IS NOT NULL, "
            "s.user_id = ?, s.announce_datetime, "
            "s.user_id, p.shares_count, p.tags, p.summary "
            "FROM posts p LEFT OUTER JOIN likes l ON "
            "l.article_id=p.global_id AND l.user_id=? "
            "LEFT OUTER JOIN follows f ON "
            "f.followed=p.author_id AND f.follower=? "
        )

    def SharedPosts(self, request, context):
        resp = db_pb.SharesResponse(
            result_type=db_pb.SharesResponse.OK
        )
        n = request.num_posts
        if not n:
            n = DEFAULT_NUM_POSTS
        user_id = -1
        sharer_id = request.sharer_id
        if request.HasField("user_global_id"):
            user_id = request.user_global_id.value
        self._logger.info('Reading {} shared posts for user feed'.format(n))
        try:
            res = self._db.execute(self._select_base +
                                   'INNER JOIN shares s ON '
                                   'p.global_id = s.article_id AND s.user_id = ? '
                                   'ORDER BY p.global_id DESC '
                                   'LIMIT ?', sharer_id, user_id, user_id, sharer_id, n)
            for tup in res:
                if not self._db_tuple_to_entry(tup, resp.results.add()):
                    del resp.results[-1]
        except sqlite3.Error as e:
            resp.result_type = db_pb.SharesResponse.ERROR
            resp.error = str(e)
            return resp
        return resp

    def _db_tuple_to_entry(self, tup, entry):
        if len(tup) != 16:
            self._logger.warning(
                "Error converting tuple to SharesEntry: " +
                "Wrong number of elements " + str(tup))
            return False
        try:
            # You'd think there'd be a better way.
            entry.global_id = tup[0]
            entry.author_id = tup[1]
            entry.title = tup[2]
            entry.body = tup[3]
            entry.creation_datetime.seconds = tup[4]
            entry.md_body = tup[5]
            entry.ap_id = tup[6]
            entry.likes_count = tup[7]
            entry.is_liked = tup[8]
            entry.is_followed = tup[9]
            entry.is_shared = tup[10]
            entry.announce_datetime.seconds = tup[11]
            entry.sharer_id = tup[12]
            entry.shares_count = tup[13]
            entry.tags = tup[14]
            entry.summary = tup[15]
        except Exception as e:
            self._logger.warning(
                "Error converting tuple to SharesEntry: " +
                str(e))
            return False
        return True

    def AddShare(self, req, context):
        self._logger.debug(
            "Adding share by %d to article %d",
            req.user_id, req.article_id
        )
        response = db_pb.SharesResponse(
            result_type=db_pb.SharesResponse.OK
        )
        try:
            self._db.execute(
                'INSERT INTO shares (user_id, article_id, announce_datetime) '
                'VALUES (?, ?, ?)',
                req.user_id,
                req.article_id,
                req.announce_datetime.seconds,
                commit=False
            )
            self._db.execute(
                'UPDATE posts SET shares_count = shares_count + 1 '
                'WHERE global_id=?',
                req.article_id
            )
        except sqlite3.Error as e:
            self._db.discard_cursor()
            self._logger.error("AddShare error: %s", str(e))
            response.result_type = db_pb.AddShareResponse.ERROR
            response.error = str(e)
        return response

    def FindShare(self, req, context):
        self._logger.debug(
            "Finding share by %d of article %d",
            req.user_id, req.article_id
        )
        resp = db_pb.FindShareResponse(
            result_type=db_pb.FindShareResponse.OK
        )
        try:
            res = self._db.execute("SELECT * " +
                                   "FROM shares s " +
                                   'WHERE s.user_id = ? AND s.article_id = ? ',
                                   req.user_id, req.article_id)
            if len(res) > 0:
                resp.exists = True
        except sqlite3.Error as e:
            resp.result_type = database_pb2.FindShareResponse.ERROR
            resp.error = str(e)
            return
        return resp
