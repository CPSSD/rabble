import json

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

    def _send(self, activ, url):
        jresp, err = self._activ_util.send_activity(activ, url)
        if err is not None:
            return err
        try:
            resp = json.loads(jresp.text)
        except json.decoder.JSONDecodeError as e:
            return str(e)
        if "success" not in resp:
            return "JSON has no success attribute"
        elif not resp["success"]:
            return resp["error"] if "error" in resp else "Foreign error"
        return None

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
        err = self._send(activity, inbox_url)
        if err is None:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK
        else:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.ERROR
            resp.error = err
        return resp
