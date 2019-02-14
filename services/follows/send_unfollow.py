import os
import sys

from services.proto import database_pb2
from services.proto import follows_pb2
from services.proto import s2s_follow_pb2


class SendUnfollowServicer:

    def __init__(self, logger, util, users_util, database_stub):
        host_name = os.environ.get("HOST_NAME")
        if not host_name:
            print("Please set HOST_NAME env variable")
            sys.exit(1)
        self._host_name = host_name
        self._logger = logger
        self._util = util
        self._users_util = users_util
        self._database_stub = database_stub

    def _remove_follow(self,
                       resp,
                       follower_id,
                       followed_id):
        # TODO(iandioch): Do not log if follow was already in state DELETED.
        match = database_pb2.Follow(follower=follower_id,
                                    followed=followed_id)

        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.DELETE,
            match=match
        )

        follow_resp = self._database_stub.Follow(req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Error setting unfollow: %s', follow_resp.error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not add requested unfollow to database'
            return resp.error

    def SendUnfollow(self, request, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info('Setting unfollow.')

        from_handle, from_instance = self._users_util.parse_username(
            request.follower)
        to_handle, to_instance = \
            self._users_util.parse_username(request.followed)
        self._logger.info('%s@%s has requested to unfollow %s@%s.',
                          from_handle,
                          from_instance,
                          to_handle,
                          to_instance)
        if to_instance is None and to_handle is None:
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not parse unfollowed username'
            return resp

        # Get user IDs for unfollow.
        follower_entry = self._users_util.get_or_create_user_from_db(
            handle=from_handle, host=from_instance)
        if follower_entry is None:
            error = 'Could not find or create user {}@{}'.format(from_handle,
                                                                 from_instance)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp
        followed_entry = self._users_util.get_or_create_user_from_db(handle=to_handle,
                                                                     host=to_instance)
        if followed_entry is None:
            error = 'Could not find or create user {}@{}'.format(to_handle,
                                                                 to_instance)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp
        self._logger.info('User ID %d has requested to unfollow User ID %d',
                          follower_entry.global_id,
                          followed_entry.global_id)

        is_foreign = to_instance is not None
        err = self._remove_follow(resp,
                                  follower_entry.global_id,
                                  followed_entry.global_id)
        if err is not None:
            # If there was an error during unfollowing, return it.
            return resp
        if is_foreign:
            # TODO(#319): Propagate unfollow to other server.
            pass
        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
