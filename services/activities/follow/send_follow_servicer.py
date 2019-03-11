from services.proto import s2s_follow_pb2

class SendFollowServicer:

    def __init__(self, logger, activ_util):
        self._logger = logger
        self._activ_util = activ_util

    def _build_activity(self, follower_actor, followed_actor):
        d = {
            "@context":  self._activ_util.rabble_context(),
            'type': 'Follow',
            'actor': follower_actor,
            'object': followed_actor,
            'to': [followed_actor],
        }
        return d

    def SendFollowActivity(self, req, context):
        resp = s2s_follow_pb2.FollowActivityResponse()
        follower_actor = self._activ_util.build_actor(
            req.follower.handle, req.follower.host)
        followed_actor = self._activ_util.build_actor(
            req.followed.handle, req.followed.host)
        activity = self._build_activity(follower_actor, followed_actor)
        inbox_url = self._activ_util.build_inbox_url(
            req.followed.handle, req.followed.host)
        self._logger.debug('Sending follow activity to foreign server')
        _, err = self._activ_util.send_activity(activity, inbox_url)
        # TODO(iandioch): See if response was what was expected.
        if err is None:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK
        else:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.ERROR
            resp.error = err
        return resp
