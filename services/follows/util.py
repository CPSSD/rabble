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

    def get_user_from_db(self, handle, host):
        self._logger.debug('User %s@%s requested from database', handle, host)
        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host
        )
        find_req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            match=user_entry
        )
        find_resp = self._db.Users(find_req)
        if len(find_resp.results) == 0:
            self._logger.warning('No user %s@%s found', handle, host)
            self._create_user_in_db(user_entry)
            return self.get_user_from_db(handle, host)
        elif len(find_resp.results) == 1:
            self._logger.debug('Found user %s@%s from database', handle, host)
            return find_resp.results[0]
        else:
            self._logger.error('> 1 user found in database for %s@%s' +
                               ', returning first one.', handle, host)
            return find_resp.results[0]

    def create_follow_in_db(self, follower_id, followed_id):
        self._logger.debug('Adding <User ID %d following User ID %d> to db.',
                           follower_id, followed_id)
        follow_entry = database_pb2.Follow(
            follower=follower_id,
            followed=followed_id
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.INSERT,
            entry=follow_entry
        )
        follow_resp = self._db.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Could not add follow to database: %s', follow_resp.error)
        return follow_resp

