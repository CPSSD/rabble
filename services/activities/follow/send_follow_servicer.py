import json

from urllib import request

from services.proto import s2s_follow_pb2


class SendFollowServicer:

    def __init__(self, logger):
        self._logger = logger

    def _build_actor(self, handle, host):
        s = f'{host}/@{handle}'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def _build_inbox_url(self, handle, host):
        # TODO(iandioch): Consider smarter way of building URL than prefixing
        # "http://" to host.
        # TODO(iandioch): Use common inbox for all activities.
        s = f'{host}/ap/@{handle}/inbox_follow'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def _build_activity(self, follower_actor, followed_actor):
        d = {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': 'Follow',
            'actor': follower_actor,
            'object': followed_actor,
            'to': [followed_actor],
        }
        return d

    def _send_activity(self, activity, target_inbox):
        body = json.dumps(activity).encode("utf-8")
        headers = {"Content-Type": "application/ld+json"}
        self._logger.info('Sending Follow to ' + target_inbox)
        req = request.Request(target_inbox,
                              data=body,
                              headers=headers,
                              method='POST')
        self._logger.debug('Sending follow activity to foreign server')
        try:
            resp = request.urlopen(req)
            # TODO(iandioch): See if response was what was expected.
            return None
        except Exception as e:
            self._logger.error('Error trying to send activity:')
            self._logger.error(str(e))
            return str(e)

    def SendFollowActivity(self, req, context):
        resp = s2s_follow_pb2.FollowActivityResponse()
        follower_actor = self._build_actor(req.follower.handle,
                                           req.follower.host)
        followed_actor = self._build_actor(req.followed.handle,
                                           req.followed.host)
        activity = self._build_activity(follower_actor, followed_actor)
        inbox_url = self._build_inbox_url(req.followed.handle,
                                          req.followed.host)
        err = self._send_activity(activity, inbox_url)
        if err is None:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK
        else:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.ERROR
            resp.error = err
        return resp
