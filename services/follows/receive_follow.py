from proto import follows_pb2


class ReceiveFollowServicer:

    def __init__(self, logger, util, users_util, database_stub):
        self._logger = logger
        self._util = util
        self._users_util = users_util
        self._database_stub = database_stub

    def ReceiveFollowRequest(self, request, context):
        resp = follows_pb2.FollowResponse()
        from_handle, from_host = resp.follower_handle, resp.follower_host
        to_handle = resp.followed
        self._logger.info('%s@%s has requested to follow %s (local user).',
                          from_handle,
                          from_instance,
                          to_handle)
        if from_host is None or from_host == '':
            error = \
                'No host associated with foreign user {}'.format(from_handle)
            self._logger.error(error)
            self._logger.error('Aborting follow request')
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp

        local_user = self._users_util.get_user_from_db(handle=to_handle,
                                                       host=None)
        if local_user is None:
            error = 'Could not find local user {}'.format(to_handle)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp

        foreign_user = \
            self._users_util.get_or_create_user_from_db(handle=from_handle,
                                                        host=from_host)
        if foreign_user is None:
            error = 'Could not find user {}@{}'.format(from_handle, from_host)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp

        self._logger.info('User ID %d has requested to follow User ID %d',
                          foreign_user.global_id,
                          local_user.global_id)

        follow_resp = self._util.create_follow_in_db(foreign_user.global_id,
                                                     local_user.global_id)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Error creating follow: %s', follow_resp.error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not add requested follow to database'
            return resp

        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
