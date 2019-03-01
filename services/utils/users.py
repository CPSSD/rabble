from services.proto import database_pb2

MAX_FIND_RETRIES = 3


class UsersUtil:

    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db = db_stub

    def _normalise_hostname(self, hostname):
        if not hostname.startswith('http'):
            self._logger.info('Normalising hostname from %s', hostname)
            hostname = 'http://' + hostname
            self._logger.info('to %s', hostname)
        return hostname

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
            # rabble instance
            if p[0].endswith('/ap'):
                p[0] = p[0][:-3]
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

    def get_or_create_user_from_db(self,
                                   handle=None,
                                   host=None,
                                   global_id=None,
                                   host_is_null=False,
                                   attempt_number=0):
        if attempt_number > MAX_FIND_RETRIES:
            self._logger.error('Retried query too many times.')
            return None

        host = self._normalise_hostname(host) if host else host
        user = self.get_user_from_db(handle, host, global_id, host_is_null)

        if user is not None:
            return user

        if global_id is not None:
            # Should not try to create a user and hope it has this ID.
            return None

        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
            host_is_null=host_is_null
        )
        self._create_user_in_db(user_entry)
        return self.get_or_create_user_from_db(handle,
                                               host,
                                               attempt_number=attempt_number + 1)

    def get_user_from_db(self, handle=None, host=None, global_id=None, host_is_null=False):
        self._logger.debug('User %s@%s (id %s) requested from database',
                           handle, host, global_id)
        host = self._normalise_hostname(host) if host else host
        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
            host_is_null=host_is_null,
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

    def get_follower_list(self, user_id):
        follow_entry = database_pb2.Follow(
            followed=user_id
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry
        )
        follow_resp = self._db.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error(
                "Find for followers of id: %s returned error: %s",
                user_id,
                follow_resp.error
            )
            return []

        return follow_resp.results

    def remove_local_users(self, followers):
        foreign_followers = []
        for follow in followers:
            follower_entry = self.get_user_from_db(
                global_id=follow.follower
            )
            if follower_entry is None:
                self._logger.error("Could not find follower in db. Id: %s", follow.follower)
                continue
            if follower_entry.host:
                foreign_followers.append(follower_entry)
        return foreign_followers
