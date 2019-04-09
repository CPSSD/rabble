import sqlite3

import util

from services.proto import database_pb2
from services.proto import database_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp


DEFAULT_NUM_POSTS = 50
CONVERT_ERROR = "Error converting tuple to PostsEntry: "


class PostsDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        # If new columns are added to the database, this query must be
        # changed. Change also _handle_insert & SearchArticles.
        self._select_base = (
            "SELECT "
            "p.global_id, p.author_id, p.title, p.body, "
            "p.creation_datetime, p.md_body, p.ap_id, p.likes_count, "
            "l.user_id IS NOT NULL, f.follower IS NOT NULL, "
            "s.user_id IS NOT NULL, p.shares_count, p.tags, p.summary "
            "FROM posts p LEFT OUTER JOIN likes l ON "
            "l.article_id=p.global_id AND l.user_id=? "
            "LEFT OUTER JOIN shares s ON "
            "s.article_id=p.global_id AND s.user_id=? "
            "LEFT OUTER JOIN follows f ON "
            "f.followed=p.author_id AND f.follower=? "
        )
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

    def InstanceFeed(self, request, context):
        resp = database_pb2.PostsResponse()
        n = request.num_posts
        if not n:
            n = DEFAULT_NUM_POSTS
        user_id = -1
        if request.HasField("user_global_id"):
            user_id = request.user_global_id.value
        self._logger.info('Reading {} posts for instance feed'.format(n))
        try:
            res = self._db.execute(self._select_base +
                                   'INNER JOIN users u '
                                   'ON p.author_id = u.global_id '
                                   'WHERE u.host IS NULL AND u.private = 0 '
                                   'ORDER BY p.global_id DESC '
                                   'LIMIT ?', user_id, user_id, user_id, n)
            for tup in res:
                if not self._db_tuple_to_entry(tup, resp.results.add()):
                    del resp.results[-1]
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return resp
        return resp

    def RandomPosts(self, request, context):
        resp = database_pb2.PostsResponse()
        n = request.num_posts
        user_id = request.user_id
        self._logger.info('Reading {} random posts'.format(n))
        try:
            res = self._db.execute(self._select_base +
                                   'WHERE l.user_id is not ? AND s.user_id is not ? '
                                   'AND p.author_id is not ?'
                                   'ORDER BY random() '
                                   'LIMIT ?', user_id, user_id, user_id,
                                   user_id, user_id, user_id, n)
            for tup in res:
                if not self._db_tuple_to_entry(tup, resp.results.add()):
                    del resp.results[-1]
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return resp
        return resp

    def TaggedPosts(self, request, context):
        resp = database_pb2.PostsResponse()
        self._logger.info('Reading all posts with tags')
        try:
            res = self._db.execute('SELECT '
                                   'p.global_id, p.tags '
                                   'FROM posts p LEFT OUTER JOIN users u ON '
                                   'p.author_id = u.global_id '
                                   'WHERE p.tags is not NULL OR p.tags = "" AND u.private = 0 '
                                   )
            for tup in res:
                entry = resp.results.add()
                if len(tup) != 2:
                    self._logger.warning(
                        CONVERT_ERROR
                        + "Wrong number of elements " + str(tup))
                    resp.result_type = database_pb2.PostsResponse.ERROR
                    resp.error = str("Wrong number of elements")
                    break
                try:
                    entry.global_id = tup[0]
                    entry.tags = tup[1]
                except Exception as e:
                    self._logger.warning(CONVERT_ERROR + str(e))
                    resp.result_type = database_pb2.PostsResponse.ERROR
                    resp.error = str(e)
                    break
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return resp
        return resp

    def SearchArticles(self, request, context):
        self._logger.info('Search query' + request.query)
        resp = database_pb2.PostsResponse()
        n = request.num_responses
        if not n:
            n = DEFAULT_NUM_POSTS
        user_id = -1
        if request.HasField("user_global_id"):
            user_id = request.user_global_id.value
        self._logger.info(
            'Reading up to {} posts for search articles'.format(n))
        try:
            res = self._db.execute(self._select_base +
                                   'WHERE global_id IN ' +
                                   '(SELECT rowid FROM posts_idx WHERE posts_idx '
                                   "MATCH ? LIMIT ?)", user_id, user_id, user_id, request.query + "*", n)
            for tup in res:
                if not self._db_tuple_to_entry(tup, resp.results.add()):
                    del resp.results[-1]
        except sqlite3.Error as e:
            self._logger.info("Error searching for posts")
            self._logger.error(str(e))
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return resp
        return resp

    def CreatePostsIndex(self, request, context):
        self._logger.info('Creating Post Index')
        resp = database_pb2.PostsResponse()
        try:
            res = self._db.execute(
                'CREATE VIRTUAL TABLE IF NOT EXISTS posts_idx USING ' +
                'fts5(title, body, content=posts, content_rowid=global_id)')
            res = self._db.execute(
                "insert into posts_idx(posts_idx) values('rebuild')")
            self._logger.info('Adding Triggers')
            res = self._db.execute(
                'CREATE TRIGGER IF NOT EXISTS posts_ai AFTER INSERT ON posts BEGIN\n' +
                '  INSERT INTO posts_idx(rowid, title, body) ' +
                'VALUES (new.global_id, new.title, new.body); \n' +
                'END;')
            res = self._db.execute(
                'CREATE TRIGGER IF NOT EXISTS posts_ad AFTER DELETE ON posts BEGIN\n' +
                '  INSERT INTO posts_idx(posts_idx, rowid, title, body) ' +
                "VALUES ('delete', old.global_id, old.title, old.body); \n" +
                'END;')
            res = self._db.execute(
                'CREATE TRIGGER IF NOT EXISTS posts_au AFTER UPDATE ON posts BEGIN\n' +
                '  INSERT INTO posts_idx(posts_idx, rowid, title, body) ' +
                "VALUES ('delete', new.global_id, new.title, new.body);\n" +
                '  INSERT INTO posts_idx(rowid, title, body) ' +
                'VALUES (new.global_id, new.title, new.body);\n' +
                'END;')
            resp.result_type = database_pb2.PostsResponse.OK
        except sqlite3.Error as e:
            self._logger.info("Error creating posts index")
            self._logger.error(str(e))
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return resp
        return resp

    def _handle_insert(self, req, resp):
        try:
            # If new columns are added to the database, this query must be
            # changed. Change also _select_base.
            self._db.execute(
                'INSERT INTO posts '
                '(author_id, title, body, creation_datetime, '
                'md_body, ap_id, likes_count, tags, summary) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                req.entry.author_id, req.entry.title,
                req.entry.body,
                req.entry.creation_datetime.seconds,
                req.entry.md_body,
                req.entry.ap_id,
                req.entry.likes_count,
                req.entry.tags,
                req.entry.summary,
                commit=False)
            res = self._db.execute(
                'SELECT last_insert_rowid() FROM posts LIMIT 1')
        except sqlite3.Error as e:
            self._db.commit()
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return
        if len(res) != 1 or len(res[0]) != 1:
            err = "Global ID data in weird format: " + str(res)
            self._logger.error(err)
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = err
            return
        resp.result_type = database_pb2.PostsResponse.OK
        resp.global_id = res[0][0]

    def _db_tuple_to_entry(self, tup, entry):
        if len(tup) != 14:
            self._logger.warning(
                CONVERT_ERROR + "Wrong number of elements " + str(tup))
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
            entry.shares_count = tup[11]
            entry.tags = tup[12]
            entry.summary = tup[13]
        except Exception as e:
            self._logger.warning(CONVERT_ERROR + str(e))
            return False
        return True

    def _handle_find(self, req, resp):
        filter_clause, values = util.equivalent_filter(req.match)
        user_id = -1
        if req.HasField("user_global_id"):
            user_id = req.user_global_id.value
        try:
            if not filter_clause:
                res = self._db.execute(
                    self._select_base, user_id, user_id, user_id)
            else:
                res = self._db.execute(
                    self._select_base +
                    "WHERE " + filter_clause +
                    " ORDER BY p.global_id DESC",
                    *([user_id, user_id, user_id] + values))
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.PostsResponse.OK
        for tup in res:
            if not self._db_tuple_to_entry(tup, resp.results.add()):
                del resp.results[-1]

    def _handle_delete(self, req, resp):
        filter_clause, values = util.equivalent_filter(req.match)
        try:
            if not filter_clause:
                res = self._db.execute('DELETE FROM posts')
            else:
                res = self._db.execute(
                    'DELETE FROM posts WHERE ' + filter_clause,
                    *values)
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.PostsResponse.OK

    def _handle_update(self, req, resp):
        # Only support updating with global_id or ap_id.
        if not req.match.global_id and not req.match.ap_id:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = "Must only filter by global_id or ap_id"
            return
        match_sql = ''
        match_val = None
        if req.match.ap_id:
            match_sql = 'ap_id = ?'
            match_val = req.match.ap_id
        else:
            match_sql = 'global_id = ?'
            match_val = req.match.global_id
        update_clause, u_values = util.entry_to_update(req.entry)
        sql = 'UPDATE posts SET ' + update_clause + ' WHERE ' + match_sql
        self._logger.info(sql)
        try:
            self._db.execute(sql, *u_values, match_val)
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.PostsResponse.OK

    def SafeRemovePost(self, req, ctx):
        if not req.global_id and not req.ap_id:
            return database_pb2.PostsResponse(
                result_type=database_pb2.PostsResponse.ERROR,
                error="Must delete by global_id or ap_id",
            )
        match_sql = ''
        match_val = None
        if req.ap_id:
            match_sql = 'posts.ap_id = ?'
            match_val = req.ap_id
        else:
            match_sql = 'posts.global_id = ?'
            match_val = req.global_id
        likes_sql = (
            'DELETE FROM likes WHERE EXISTS (' +
            'SELECT * FROM posts WHERE ' +
            'likes.article_id = posts.global_id AND ' +
            match_sql + ')'
        )
        shares_sql = (
            'DELETE FROM shares WHERE EXISTS (' +
            'SELECT * FROM posts WHERE ' +
            'shares.article_id = posts.global_id AND ' +
            match_sql + ')'
        )
        posts_sql = 'DELETE FROM posts WHERE ' + match_sql
        try:
            self._db.execute(likes_sql, match_val, commit=False)
            self._db.execute(shares_sql, match_val, commit=False)
            self._db.execute(posts_sql, match_val)
        except sqlite3.Error as e:
            return database_pb2.PostsResponse(
                result_type=database_pb2.PostsResponse.ERROR,
                error=str(e),
            )
        return database_pb2.PostsResponse(
            result_type=database_pb2.PostsResponse.OK,
        )

