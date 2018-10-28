import sqlite3

import util

import database_pb2


class UsersDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._users_type_handlers = {
            database_pb2.UsersRequest.INSERT: self._users_handle_insert,
            database_pb2.UsersRequest.FIND: self._users_handle_find.
        }

    def _db_tuple_to_entry(self, tup, entry):
        if len(tup) != 4:
            self._logger.warning(
                "Error converting tuple to UsersEntry: " +
                "Wrong number of elements " + str(tup))
            return False
        try:
            # You'd think there'd be a better way.
            entry.handle = tup[0]
            entry.display_name = tup[1]
            entry.host = tup[2]
            entry.global_id = tup[3]
        except Exception as e:
            self._logger.warning(
                "Error converting tuple to UsersEntry: " +
                str(e))
            return False
        return True


    def Users(self, request, context):
        response = database_pb2.UsersResponse()
        self._users_type_handlers[request.request_type](request, response)
        return response

    def _users_handle_insert(self, req, resp):
        self._logger.info('Inserting new user into Users database.')
        # TODO(iandioch): Ensure we're not overwriting a previous user.
        try:
            self._db.execute(
                'INSERT INTO users '
                '(handle, host, display_name) '
                'VALUES (?, ?)',
                req.entry.handle,
                req.entry.host,
                req.entry.display_name)
        except sqlite3.Error as e:
            self._logger.error(str(e))
            resp.result_type = database_pb2.UsersResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.UsersResponse.OK

    def _users_handle_find(self, req, resp):
        filter_clause, values = util.entry_to_filter(req.match)
        try:
            if not filter_clause:
                res = self._db.execute('SELECT * FROM users')
            else:
                res = self._db.execute(
                    'SELECT * FROM users WHERE ' + filter_clause,
                    *values)
        except sqlite3.Error as e:
            resp.result_type = database_pb2.UsersResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.UsersResponse.OK
        for tup in res:
            if not self._db_tuple_to_entry(tup, resp.results.add()):
                del resp.results[-1]
