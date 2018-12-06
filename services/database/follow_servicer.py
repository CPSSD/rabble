import sqlite3

import util

from services.proto import database_pb2


class FollowDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._follow_type_handlers = {
            database_pb2.DbFollowRequest.INSERT: self._follow_handle_insert,
            database_pb2.DbFollowRequest.FIND: self._follow_handle_find,
            database_pb2.DbFollowRequest.UPDATE: self._follow_handle_update,
        }

    def _db_tuple_to_entry(self, tup, entry):
        if len(tup) != 3:
            self._logger.warning(
                "Error converting tuple to Follow: " +
                "Wrong number of elements " + str(tup))
            return False
        try:
            # You'd think there'd be a better way.
            entry.follower = tup[0]
            entry.followed = tup[1]
            entry.state = tup[2]
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
        # Make sure that we always set state with a default value of ACTIVE.
        state = req.entry.state
        if state == None:
            state = database_pb2.Follow.ACTIVE
        try:
            self._db.execute(
                'INSERT INTO follows '
                '(follower, followed, state) '
                'VALUES (?, ?, ?)',
                req.entry.follower,
                req.entry.followed,
                state)
        except sqlite3.Error as e:
            self._logger.error(str(e))
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.DbFollowResponse.OK

    def _follow_handle_find(self, req, resp):
        default = [("state", database_pb2.Follow.ACTIVE)]
        filter_clause, values = util.equivalent_filter(req.match, default)
        try:
            if not filter_clause:
                # Since we set a default match, this should never happen.
                err = 'Query {} not allowed for follows'.format(
                    'SELECT * FROM follows',
                )
                self._logger.warning(err)
                resp.result_type = database_pb2.DbFollowResponse.ERROR
                resp.error = err
                return
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

    def _follow_handle_update(self, req, resp):
        if not req.HasField("match") or not req.HasField("entry"):
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            resp.error = "bad parameters: please set both match and entry"
            return

        if not req.match.follower or not req.match.followed:
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            resp.error = "bad parameters: please set both follower and followed"
            return

        filter_clause, values = util.equivalent_filter(req.match)
        if not filter_clause:
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            resp.error = "could not create filter for UPDATE"
            return

        try:
            # since we only update state we can hardcode that paramater
            query = 'UPDATE follows SET state = ? WHERE ' + filter_clause
            valstr = str(req.entry.state) + ", " + ', '.join(str(v)
                                                             for v in values)
            count = self._db.execute_count(query, req.entry.state, *values)
        except sqlite3.Error as e:
            self._logger.warning('Got error writing to DB: ' + str(e))
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            resp.error = str(e)
            return

        if count != 1:
            err = 'UPDATE affected {} rows, expected 1'.format(count)
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            self._logger.wanring(err)
            resp.error = err

        resp.result_type = database_pb2.DbFollowResponse.OK
