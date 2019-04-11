from services.proto import approver_pb2


class SendApprovalServicer:
    def __init__(self, logger, activ_util, users_util):
        self._logger = logger
        self._activ_util = activ_util
        self._users_util = users_util

    def _build_activity(self, req):
        actor = self._activ_util.build_actor
        followed = actor(req.follow.followed.handle, req.follow.followed.host)
        follower = actor(req.follow.follower.handle, req.follow.follower.host)
        activity_type = 'Accept' if req.accept else 'Reject'

        return {
            '@context': self._activ_util.rabble_context(),
            'type': activity_type,
            'actor': followed,
            'object': {
                'type': 'Follow',
                'actor': follower,
                'object': followed,
            },
            'to': [follower],
        }

    def _get_local_user_id(self, handle):
        user = self._users_util.get_user_from_db(handle=handle,
                                                 host_is_null=True)
        if user is None:
            return None
        return user.global_id

    def SendApproval(self, req, context):
        resp = approver_pb2.ApprovalResponse()
        url = self._activ_util.build_inbox_url(req.follow.follower.handle,
                                               req.follow.follower.host)
        activity = self._build_activity(req)

        sender_id = self._get_local_user_id(req.follow.followed.handle)
        _, err = self._activ_util.send_activity(activity,
                                                url,
                                                sender_id=sender_id)
        if err is not None:
            resp.error = err
            resp.result_type = approver_pb2.ApprovalResponse.ERROR

        return resp
