from proto import database_pb2
from proto import follows_pb2


class SendFollowServicer:

    def __init__(self, logger, util, users_util, database_stub):
        self._logger = logger
        self._util = util
        self._users_util = users_util
        self._database_stub = database_stub

    def SendFollowRequest(self, request, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info('Send follow request.')

        from_handle, from_instance = self._users_util.parse_username(
            request.follower)
        to_handle, to_instance = \
            self._users_util.parse_username(request.followed)
        self._logger.info('%s@%s has requested to follow %s@%s.',
                          from_handle,
                          from_instance,
                          to_handle,
                          to_instance)
        if to_instance is None and to_handle is None:
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not parse followed username'
            return resp

        # Get user IDs for follow.
        follower_entry = self._users_util.get_user_from_db(
            handle=from_handle, host=from_instance)
        if follower_entry is None:
            error = 'Could not find or create user {}@{}'.format(from_handle,
                                                                 from_instance)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp
        followed_entry = self._users_util.get_user_from_db(handle=to_handle,
                                                           host=to_instance)
        if followed_entry is None:
            error = 'Could not find or create user {}@{}'.format(to_handle,
                                                                 to_instance)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp
        self._logger.info('User ID %d has requested to follow User ID %d',
                          follower_entry.global_id,
                          followed_entry.global_id)

        follow_resp = self._util.create_follow_in_db(follower_entry.global_id,
                                                     followed_entry.global_id)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Error creating follow: %s', follow_resp.error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not add requested follow to database'
            return resp

        # TODO(#61): Send Follow activity if followed user is not local.

        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
