from services.proto import follows_pb2
from services.proto import database_pb2
from services.proto import s2s_follow_pb2
from services.proto import approver_pb2


class Util:

    def __init__(self, logger, db_stub, approver_stub, users_util):
        self._logger = logger
        self._db = db_stub
        self._approver_stub = approver_stub
        self._users_util = users_util

    def create_follow_in_db(self, follower_id, followed_id,
                            state=database_pb2.Follow.ACTIVE):
        self._logger.debug('Adding <User ID %d following User ID %d> to db.',
                           follower_id, followed_id)
        follow_entry = database_pb2.Follow(
            follower=follower_id,
            followed=followed_id,
            state=state,
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

    def delete_follow_in_db(self, follower_id, followed_id):
        self._logger.debug('Deleting <User ID %d following User ID %d> from db.',
                           follower_id, followed_id)
        follow_entry = database_pb2.Follow(
            follower=follower_id,
            followed=followed_id,
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.DELETE,
            match=follow_entry
        )
        follow_resp = self._db.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Could not delete follow from database: %s',
                               follow_resp.error)
        return follow_resp

    def get_follows(self, follower_id=None, followed_id=None):
        self._logger.debug('Finding follows <User ID %s following User ID %s>',
                           ('*' if (follower_id is None) else str(follower_id)),
                           ('*' if (followed_id is None) else str(followed_id)))
        follow_entry = database_pb2.Follow(
            follower=follower_id,
            followed=followed_id
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry
        )
        follow_resp = self._db.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Could not add follow to database: %s',
                               follow_resp.error)
        return follow_resp

    def convert_db_user_to_follow_user(self, db_user, follow_user):
        self._logger.warning('Converting db user %s@%s to follow user.',
                             db_user.handle, db_user.host)
        try:
            follow_user.handle = db_user.handle
            follow_user.host = db_user.host
            follow_user.display_name = db_user.display_name
        except Exception as e:
            self._logger.warning('Error converting db user to follow user: ' +
                                 str(e))
            return False
        return True

    def attempt_to_accept(self, local_user, foreign_user, host_name, is_accepted):
        s2s_follow = s2s_follow_pb2.FollowDetails(
            follower = s2s_follow_pb2.FollowActivityUser(
                handle = foreign_user.handle,
                host = foreign_user.host,
            ),
            followed = s2s_follow_pb2.FollowActivityUser(
                handle = local_user.handle,
                host = host_name,
            ),
        )
        req = approver_pb2.Approval(
                accept=is_accepted,
                follow=s2s_follow,
        )
        # TODO(devoxel): Add response logic
        print(self._approver_stub.SendApproval(req))

    def validate_and_get_users(self, resp, request):
        """
        _validate_and_get_users validates request fields and finds the
        requested users. It takes as an argument the response field, and
        handles errors if they should happen.
        Returns:
          local_user, foreign_user
          If either is None, then the request has failed and the error has
          already been written.
        """
        from_handle, from_host = request.follower_handle, request.follower_host
        to_handle = request.followed

        self._logger.info('%s@%s has requested to follow %s (local user).',
                          from_handle,
                          from_host,
                          to_handle)

        if from_host is None or from_host == '':
            error = \
                'No host associated with foreign user {}'.format(from_handle)
            self._logger.error(error)
            self._logger.error('Aborting follow request')
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return None, None

        local_user = self._users_util.get_user_from_db(handle=to_handle,
                                                       host_is_null=True)
        if local_user is None:
            error = 'Could not find local user {}'.format(to_handle)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return None, None

        foreign_user = self._users_util.get_or_create_user_from_db(
            handle=from_handle,
            host=from_host)

        if foreign_user is None:
            error = 'Could not find user {}@{}'.format(from_handle, from_host)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return local_user, None
        return local_user, foreign_user
