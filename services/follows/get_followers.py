import database_pb2
import follows_pb2


class SendFollowServicer:

    def __init__(self, logger, util, database_stub):
        self._logger = logger
        self._util = util
        self._database_stub = database_stub

    def GetFollowers(self, request, context):
        self._logger.debug('List of followers of %s requested', request.username)
        resp = follows_pb2.GetFollowersReponse()

        handle, host = self._util.parse_username(
            request.username)
        if handle is None and host is None:
            resp.result_type = follows_pb2.GetFollowersResponse.ERROR
            resp.error = 'Could not parse queried username'
            return resp

        # Get user IDs for follow.
        user_entry = self._util.get_user_from_db(handle, host)
        if user_entry is None:
            error = 'Could not find or create user {}@{}'.format(from_handle,
                                                                 from_instance)
            self._logger.error(error)
            resp.result_type = follows_pb2.GetFollowersResponse.ERROR
            resp.error = error
            return resp

        user_id = user_entry.global_id

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
