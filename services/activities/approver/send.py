from services.proto import approver_pb2

class SendApprovalServicer:
    def __init__(self, logger, activ_util):
        self._logger = logger
        self._activ_util = activ_util

    def _build_activity(self, req):
        actor = self._activ_util.build_actor
        followed = actor(req.follow.followed.handle, req.follow.followed.host)
        follower = actor(req.follow.follower.handle, req.follow.follower.host)
        activity_type = 'accept' if req.accept else 'deny'

        return {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': activity_type,
            'actor': followed,
            'object': {
                'type': 'Follow',
                'actor': follower,
                'object': followed,
            },
            'to': [follower],
        }

    def SendApproval(self, req, context):
        resp = approver_pb2.ApprovalResponse()
        url = self._activ_util.build_inbox_url(req.follow.follower.handle,
                                               req.follow.follower.host)
        activity = self._build_activity(req)
        _, err = self._activ_util.send_activity(activity, url)
        if err is not None:
            resp.error = err
            resp.result_type = approver_pb2.ApprovalResponse.ERROR

        return resp
