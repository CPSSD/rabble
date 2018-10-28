import follows_pb2
import database_pb2

MAX_FIND_RETRIES = 3


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

    def get_user_from_db(self,
                        handle=None,
                        host=None,
                        global_id=None,
                        attempt_number=0):
        if attempt_number > MAX_FIND_RETRIES:
            self._logger.error('Retried query too many times.')
            return None
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
            if global_id is not None:
                # Should not try to create a user and hope it has this ID.
                return None
            self._create_user_in_db(user_entry)
            return self.get_user_from_db(handle, host,
                                         attempt_number=attempt_number + 1)
        elif len(find_resp.results) == 1:
            self._logger.debug('Found user %s@%s (id %s) from database',
                               handle, host, global_id)
            return find_resp.results[0]
        else:
            self._logger.error('> 1 user found in database for %s@%s (id %s)' +
                               ', returning first one.',
                               handle, host, global_id)
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
            self._logger.error('Could not add follow to database: %s',
                               follow_resp.error)
        return follow_resp

    def get_follows(self, follower_id=None, followed_id=None):
        self._logger.debug('Finding follows <User ID %s following User ID %s>',
                           ('*' if (follower_id is None) else str(follower_id)),
                           ('*' if (followed_id is None) else str(followed_id)))
        follow_entry=database_pb2.Follow(
            follower=follower_id,
            followed=followed_id
        )
        follow_req=database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry
        )
        follow_resp=self._db.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Could not add follow to database: %s',
                               follow_resp.error)
        return follow_resp

    def convert_db_user_to_follow_user(self, db_user, follow_user):
        self._logger.warning('Trying to convert %s %s', db_user.handle, db_user.host)
        try:
            follow_user.handle=db_user.handle
            follow_user.host=db_user.host
            follow_user.display_name=db_user.display_name
        except Exception as e:
            self._logger.warning('Error converting db user to follow user: ' +
                                 str(e))
            return False
        return True
