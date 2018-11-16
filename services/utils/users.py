from proto import database_pb2

MAX_FIND_RETRIES = 3


class UsersUtil:

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

    # Parse actor string. This is a the url of the actor object of
    # a user of a local/foreign instance
    def parse_actor(self, actor_uri):
        actor_uri = actor_uri.lstrip('/@')
        p = actor_uri.split('/@')
        if len(p) == 2:
            # Actor uri like 'rabbleinstance.com/@admin'
            return tuple(p)
        # Username is incorrect/malicious/etc.
        self._logger.warning('Couldn\'t parse actor %s', actor_uri)
        return None, None

    def _create_user_in_db(self, entry):
        self._logger.debug('Creating user %s@%s in database',
                           entry.handle, entry.host)
        insert_req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.INSERT,
            entry=entry
        )
        insert_resp = self._db.Users(insert_req)
        # TODO(iandioch): Respond to errors.
        return insert_resp

    def get_or_create_user_from_db( self,
                                    handle=None,
                                    host=None,
                                    global_id=None,
                                    attempt_number=0):
        if attempt_number > MAX_FIND_RETRIES:
            self._logger.error('Retried query too many times.')
            return None

        user = self.get_user_from_db(handle, host, global_id)

        if user is not None:
            return user

        if global_id is not None:
            # Should not try to create a user and hope it has this ID.
            return None

        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host
        )
        self._create_user_in_db(user_entry)
        return self.get_or_create_user_from_db( handle,
                                                host,
                                                attempt_number=attempt_number + 1)

    def get_user_from_db(self,
                         handle=None,
                         host=None,
                         global_id=None):
        self._logger.debug('User %s@%s (id %s) requested from database',
                           handle, host, global_id)
        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
            global_id=global_id
        )
        find_req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            match=user_entry
        )
        find_resp = self._db.Users(find_req)
        if len(find_resp.results) == 0:
            self._logger.warning('No user %s@%s (id %s) found',
                                 handle, host, global_id)
            return None
        elif len(find_resp.results) == 1:
            self._logger.debug('Found user %s@%s (id %s) from database',
                               handle, host, global_id)
            return find_resp.results[0]
        else:
            self._logger.error('> 1 user found in database for %s@%s (id %s)' +
                               ', returning first one.',
                               handle, host, global_id)
            return find_resp.results[0]
