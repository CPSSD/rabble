import sqlite3

import util

from services.proto import database_pb2
from services.proto import database_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp


DEFAULT_NUM_POSTS = 50


class PostsDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
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
        self._logger.info('Reading {} posts for instance feed'.format(n))
        try:
            # TODO(iandioch): Fix user host insertion. Below query should have
            # 'WHERE users.host IS NULL' and not 'WHERE users.host = ""'.

            # If new columns are added to the database, this query must be
            # changed. Change also _handle_insert.
            res = self._db.execute('SELECT posts.global_id, author_id, title, '
                                   'body, creation_datetime, md_body, ap_id, '
                                   'likes_count '
                                   'FROM posts '
                                   'INNER JOIN users '
                                   'ON posts.author_id = users.global_id '
                                   'WHERE users.host = "" AND users.private = 0 '
                                   'ORDER BY posts.global_id DESC '
                                   'LIMIT {} '.format(n))
            for tup in res:
                if not self._db_tuple_to_entry(tup, resp.results.add()):
                    del resp.results[-1]
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return resp
        return resp

    def _handle_insert(self, req, resp):
        try:
            # If new columns are added to the database, this query must be
            # changed. Change also InstanceFeed.
            self._db.execute(
                'INSERT INTO posts '
                '(author_id, title, body, creation_datetime, '
                'md_body, ap_id, likes_count) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                req.entry.author_id, req.entry.title,
                req.entry.body,
                req.entry.creation_datetime.seconds,
                req.entry.md_body,
                req.entry.ap_id,
                req.entry.likes_count,
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
        if len(tup) != 8:
            self._logger.warning(
                "Error converting tuple to PostsEntry: " +
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
        except Exception as e:
            self._logger.warning(
                "Error converting tuple to PostsEntry: " +
                str(e))
            return False
        return True

    def _handle_find(self, req, resp):
        filter_clause, values = util.equivalent_filter(req.match)
        try:
            if not filter_clause:
                res = self._db.execute('SELECT * FROM posts')
            else:
                res = self._db.execute(
                    'SELECT * FROM posts WHERE ' + filter_clause +
                    ' ORDER BY posts.global_id DESC ',
                    *values)
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
        # Only support updating ap_id from global_id for now.
        if not req.match.global_id or not req.entry.ap_id:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = "Must only filter by global_id and set ap_id"
            return
        try:
            self._db.execute(
                'UPDATE posts SET ap_id=? WHERE global_id=?',
                req.entry.ap_id, req.match.global_id
            )
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PostsResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.PostsResponse.OK
