from services.proto import approver_pb2
from services.proto import database_pb2


class ReceiveApprovalServicer:
    def __init__(self, logger, db_stub, users_util):
        self._logger = logger
        self._db_stub = db_stub
        self._users_util = users_util

    def _get_users(self, resp, req):
        # TODO(devoxel): figure out if we should validate req.follower.host
        _, handle = self._users_util.parse_actor(req.follow.follower)
        follower = self._users_util.get_user_from_db(handle=handle,
                                                     host_is_null=True)
        if follower is None:
            err = "Could not find local follower {} in db".format(handle)
            self._logger.error(err)
            resp.error = err
            resp.result_type = approver_pb2.ApprovalResponse.ERROR
            return None, None

        host, foreign_handle = self._users_util.parse_actor(
            req.follow.followed)

        # TODO(devoxel): This should probably be in a util function.
        if 'http' in host:
            host = host.split("//", maxsplit=2)[1]

        followed = self._users_util.get_user_from_db(handle=foreign_handle,
                                                     host=host)
        if followed is None:
            err = "Could not find followed {}@{} in db".format(foreign_handle,
                                                               host)
            self._logger.error(err)
            resp.error = err
            resp.result_type = approver_pb2.ApprovalResponse.ERROR
            return follower, None

        return follower, followed

    def _update_follow(self, follower_id, followed_id, state):
        entry = database_pb2.Follow(follower=follower_id,
                                    followed=followed_id,
                                    state=state)

        match = database_pb2.Follow(follower=follower_id,
                                    followed=followed_id,
                                    state=database_pb2.Follow.PENDING)

        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.UPDATE,
            match=match,
            entry=entry,
        )

        return self._db_stub.Follow(req)

    def _set_approved(self, follower, followed):
        return self._update_follow(follower.global_id,
                                   followed.global_id,
                                   database_pb2.Follow.ACTIVE)

    def _set_rejected(self, follower, followed):
        return self._update_follow(follower.global_id,
                                   followed.global_id,
                                   database_pb2.Follow.REJECTED)

    def ReceiveApproval(self, req, context):
        self._logger.info("Received an approval request")
        resp = approver_pb2.ApprovalResponse()

        follower, followed = self._get_users(resp, req)
        if follower is None or followed is None:
            return resp

        db_resp = None
        if req.accept:
            db_resp = self._set_approved(follower, followed)
        else:
            db_resp = self._set_rejected(follower, followed)

        if db_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            err = "Could not add follow to database: " + db_resp.error
            self._logger.error(err)
            resp.error = err
            resp.result_type = approver_pb2.ApprovalResponse.ERROR
            return resp

        resp.result_type = approver_pb2.ApprovalResponse.OK
        return resp
