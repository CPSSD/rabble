import database_pb2
import follows_pb2


class SendFollowServicer:

    def __init__(self, logger, util, database_stub):
        self._logger = logger
        self._util = util
        self._database_stub = database_stub

    def SendFollowRequest(self, request, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info('Send follow request.')

        from_handle, from_instance = self._util.parse_username(
            request.follower)
        to_handle, to_instance = self._util.parse_username(request.followed)
        self._logger.info('%s@%s has requested to follow %s@%s.',
                          from_handle,
                          from_instance,
                          to_handle,
                          to_instance)
        if to_instance is None and to_handle is None:
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not parse followed username'
            return resp

        if to_instance is None:
            # TODO(iandioch): Handle local follows
            resp.result_type = follows_pb2.FollowResponse.OK
            return resp

        # TODO(iandioch): Handle remote follows.
        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
