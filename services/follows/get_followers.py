import database_pb2
import follows_pb2


class SendFollowServicer:

    def __init__(self, logger, util, database_stub):
        self._logger = logger
        self._util = util
        self._database_stub = database_stub

    def GetFollowers(self, request, context):
        self._logger.debug('List of followers of %s requested',
                           request.username)
        resp = follows_pb2.GetFollowersReponse()

        handle, host = self._util.parse_username(
            request.username)
        if handle is None and host is None:
            resp.result_type = follows_pb2.GetFollowersResponse.ERROR
            resp.error = 'Could not parse queried username'
            return resp

        following_ids = util.get_follows(followed_id)

        for _id in following_ids:
            user = self._util.get_user_from_db(global_id = _id)
            if user is None:
                self._logger.warning('Could not find following user for id %d',
                                     _id)
                continue
            if self._util.convert_db_user_to_follow_user(user,
                                                         resp.results.add()):
                self._logger.warning('Could not conver user %s@%s to ' +
                                     'FollowUser', user.handle, user.host)

        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
