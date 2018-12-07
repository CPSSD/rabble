import sqlite3

import util

from services.proto import database_pb2


class UsersDatabaseServicer:

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger
        self._users_type_handlers = {
            database_pb2.UsersRequest.INSERT: self._users_handle_insert,
            database_pb2.UsersRequest.FIND: self._users_handle_find,
            database_pb2.UsersRequest.FIND_NOT: self._users_handle_find_not,
            database_pb2.UsersRequest.UPDATE: self._users_handle_update,
        }

    def _db_tuple_to_entry(self, tup, entry):
        if len(tup) != 8:
            self._logger.warning(
                "Error converting tuple to UsersEntry: " +
                "Wrong number of elements " + str(tup))
            return False
        try:
            # Tuple items are in order of columns of Users table in db.
            entry.global_id = tup[0]
            entry.handle = tup[1]
            entry.host = tup[2]
            entry.display_name = tup[3]
            entry.password = tup[4]
            entry.bio = tup[5]
            entry.rss = tup[6]
            entry.private = tup[7]
        except Exception as e:
            self._logger.warning(
                "Error converting tuple to UsersEntry: " +
                str(e))
            return False
        return True

    def PendingFollows(self, request, context):
        resp = database_pb2.PendingFollowResponse()

        try:
            user_res = self._db.execute('SELECT global_id FROM users '
                                        'WHERE handle = ? AND host = ""',
                                        request.handle)
            if len(user_res) != 1 or len(user_res[0]) != 1:
                resp.result_type = database_pb2.PendingFollowResponse.ERROR
                resp.error = 'couldnt get user response, users: ' + str(user_res)
                return resp
            user_id = user_res[0][0]
            res = self._db.execute('SELECT handle, host FROM users '
                                   'INNER JOIN follows '
                                   'ON users.global_id = follows.follower '
                                   'WHERE follows.followed = ? AND follows.state = ? '
                                   'ORDER BY users.global_id DESC',
                                   user_id, database_pb2.Follow.PENDING)
        except sqlite3.Error as e:
            resp.result_type = database_pb2.PendingFollowResponse.ERROR
            resp.error = str(e)
            return resp

        for tup in res:
            if len(tup) != 2:
                resp.result_type = database_pb2.PendingFollowResponse.ERROR
                resp.error = 'bad database resposne, got mis-sized tuple ' + str(tup)
                return
            resp.followers.add(handle = tup[0], host = tup[1])
        return resp

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
                '(handle, host, display_name, password, bio, rss, private) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                req.entry.handle,
                req.entry.host,
                req.entry.display_name,
                req.entry.password,
                req.entry.bio,
                req.entry.rss,
                req.entry.private)
        except sqlite3.Error as e:
            self._logger.info("Error inserting")
            self._logger.error(str(e))
            resp.result_type = database_pb2.UsersResponse.ERROR
            resp.error = str(e)
            return
        resp.result_type = database_pb2.UsersResponse.OK

    def _users_handle_update(self, req, resp):
        update_clause, u_values = util.entry_to_update(req.entry)
        filter_clause, f_values = util.equivalent_filter(req.match)
        values = u_values + f_values

        if not filter_clause or not update_clause:
            self._logger.info("Could not generate update SQL: "
                              "filter_clause: '%s', update_clause: '%s'",
                              filter_clause, update_clause)
            resp.result_type = database_pb2.UsersResponse.ERROR
            resp.error = "Bad input: could not generate SQL."
            return

        sql = "UPDATE users SET " +  update_clause  + " WHERE " +  filter_clause
        valstr = ', '.join(str(v) for v in values)
        self._logger.debug('Running query "%s" with values (%s)', sql, valstr)

        try:
            count = self._db.execute_count(sql, *values)
        except sqlite3.Error as e:
            resp.result_type = database_pb2.UsersResponse.ERROR
            resp.error = str(e)
            return

        if count != 1:
            err = 'UPDATE affected {} rows, expected 1'.format(count)
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            self._logger.warning(err)
            resp.error = err

        resp.result_type = database_pb2.UsersResponse.OK

    def _users_handle_find_not(self, req, resp):
        filter_clause, values = util.not_equivalent_filter(req.match)
        self._user_find_op(resp, filter_clause, [])

    def _users_handle_find(self, req, resp):
        filter_clause, values = util.equivalent_filter(req.match)
        self._user_find_op(resp, filter_clause, values)

    def _user_find_op(self, resp, filter_clause, values):
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
        return resp
