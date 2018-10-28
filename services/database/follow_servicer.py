import sqlite3

import util

import database_pb2


class FollowDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._follow_type_handlers = {
            database_pb2.DbFollowRequest.INSERT: self._follow_handle_insert,
            database_pb2.DbFollowRequest.FIND: self._follow_handle_find,
        }

    def _db_tuple_to_entry(self, tup, entry):
        if len(tup) != 2:
            self._logger.warning(
                "Error converting tuple to Follow: " +
                "Wrong number of elements " + str(tup))
            return False
        try:
            # You'd think there'd be a better way.
            entry.follower = tup[0]
            entry.followed = tup[1]
        except Exception as e:
            self._logger.warning(
                "Error converting tuple to Follow: " +
                str(e))
            return False
        return True

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

    def _follow_handle_find(self, req, resp):
        filter_clause, values = util.entry_to_filter(req.match)
        try:
            if not filter_clause:
                query = 'SELECT * FROM follows'
                self._logger.debug('Running query "%s"', query)
                res = self._db.execute(query)
            else:
                query = 'SELECT * FROM follows WHERE ' + filter_clause
                valstr = ', '.join(str(v) for v in values)
                self._logger.debug('Running query "%s" with values (%s)',
                                   query, valstr)
                res = self._db.execute(query, *values)
        except sqlite3.Error as e:
            self._logger.warning('Got error reading DB: ' + str(e))
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.DbFollowResponse.OK
        for tup in res:
            if not self._db_tuple_to_entry(tup, resp.results.add()):
                del resp.results[-1]

        self._logger.debug('%d results of follower query.', len(resp.results))
