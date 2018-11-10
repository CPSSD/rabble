from enum import Enum

from proto import database_pb2
from proto import follows_pb2


class GetFollowsReceiver:

    def __init__(self, logger, util, users_util, database_stub):
        self._logger = logger
        self._util = util
        self._users_util = users_util
        self._database_stub = database_stub
        self.RequestType = Enum('RequestType', 'FOLLOWING FOLLOWERS')

    def _get_follows(self, request, context, request_type):
        if request_type == self.RequestType.FOLLOWERS:
            self._logger.debug('List of followers of %s requested',
                               request.username)
        else:
            self._logger.debug('List of users %s is following requested',
                               request.username)
        resp = follows_pb2.GetFollowsResponse()

        # Parse input username
        handle, host = self._users_util.parse_username(
            request.username)
        if handle is None and host is None:
            resp.result_type = follows_pb2.GetFollowsResponse.ERROR
            resp.error = 'Could not parse queried username'
            return resp

        # Get user obj associated with given user handle & host from database
        user_entry = self._users_util.get_user_from_db(handle, host)
        if user_entry is None:
            error = 'Could not find or create user {}@{}'.format(from_handle,
                                                                 from_instance)
            self._logger.error(error)
            resp.result_type = follows_pb2.GetFollowersResponse.ERROR
            resp.error = error
            return resp
        user_id = user_entry.global_id

        # Get followers/followings for this user.
        following_ids = None
        if request_type == self.RequestType.FOLLOWERS:
            following_ids = self._util.get_follows(followed_id=user_id).results
        else:
            following_ids = self._util.get_follows(follower_id=user_id).results

        # Convert other following users and add to output proto.
        for following_id in following_ids:
            _id = following_id.followed
            if request_type == self.RequestType.FOLLOWERS:
                _id = following_id.follower
            user = self._users_util.get_user_from_db(global_id=_id)
            if user is None:
                self._logger.warning('Could not find user for id %d',
                                     _id)
                continue

            ok = self._util.convert_db_user_to_follow_user(user,
                                                           resp.results.add())
            if not ok:
                self._logger.warning('Could not convert user %s@%s to ' +
                                     'FollowUser', user.handle, user.host)

        resp.result_type = follows_pb2.GetFollowsResponse.OK
        return resp

    def GetFollowing(self, request, context):
        self._logger.debug('GetFollowing, username = %s', request.username)
        return self._get_follows(request, context, self.RequestType.FOLLOWING)

    def GetFollowers(self, request, context):
        self._logger.debug('GetFollowers, username = %s', request.username)
        return self._get_follows(request, context, self.RequestType.FOLLOWERS)
