import database_pb2

class Util:

    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db = db_stub

    def parse_username(self, username):
        username = username.lstrip('@')
        p = username.split('@')
        if len(p) == 1:
            # Local user like 'admin'.
            return p[0], None
        if len(p) == 2:
            # Foreign user like 'admin@rabbleinstance.com'
            return tuple(p)
        # Username is incorrect/malicious/etc.
        self._logger.warning('Couldn\'t parse username %s', username)
        return None, None

    def get_user_from_db(self, handle, host):
        self._logger.debug('User %s@%s requested from database', handle, host)
        user_entry = database_pb2.UsersEntry(
            handle = handle,
            host = host
        )
        find_req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            entry = user_entry
        )
        find_resp = self._db.Users(find_req)
        if len(find_resp.results) == 0:
            self._logger.warning('No user %s@%s found', handle, host)
        elif len(find_resp.results) == 1:
            self._logger.debug('Found user %s@%s from database', handle, host)
            return find_resp.results[0]
        else:
            self._logger.error('> 1 user found in database for %s@%s' + \
                               ', returning first one.', handle, host)
            return find_resp.results[0]
