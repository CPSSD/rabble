import os
import sys

from services.proto import database_pb2
from services.proto import follows_pb2

class AcceptFollowServicer:
    def __init__(self, logger, util, users_util, db_stub):
        self._logger = logger
        self._util = util
        self._users_util = users_util
        self._db_stub = db_stub
        self._host_name = os.environ.get("HOST_NAME")
        if not self._host_name:
            print("Please set HOST_NAME env variable")
            sys.exit(1)

    def _get_users(self, resp, request):
        followed = self._users_util.get_user_from_db(handle=request.handle)
        if not followed:
            self._logger.error('Could not find followed user.')
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not find followed user. You do not exist!'
            return None, None

        follower = self._users_util.get_user_from_db(handle=request.follower.handle,
                                                    host=request.follower.host)
        if not follower:
            self._logger.error('Could not find follower.')
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not find follower.'
            return None, None
        return follower, followed

    def _get_follow(self, resp, follower_id, followed_id):
        match = database_pb2.Follow(follower=follower_id,
                                    followed=followed_id,
                                    state=database_pb2.Follow.PENDING)

        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=match,
        )

        resp = self._db_stub.Follow(req)
        if resp.result_type == database_pb2.DbFollowResponse.ERROR:
            err = "Could not get follow database: " + resp.error
            self._logger.error(err)
            resp.error = err
            resp.result_type = database_pb2.FollowResponse.ERROR
            return err

    def _modify_follow(self, resp, follower_id, followed_id, is_accepted):
        entry = database_pb2.Follow(follower=follower_id,
                                    followed=followed_id)
        if is_accepted:
            entry.state = database_pb2.Follow.ACTIVE
        else:
            entry.state = database_pb2.Follow.REJECTED

        match = database_pb2.Follow(follower=follower_id,
                                    followed=followed_id,
                                    state=database_pb2.Follow.PENDING)

        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.UPDATE,
            match=match,
            entry=entry,
        )

        resp = self._db_stub.Follow(req)
        if resp.result_type == database_pb2.DbFollowResponse.ERROR:
            err = "Could not modify follow: " + resp.error
            self._logger.error(err)
            resp.error = err
            resp.result_type = database_pb2.FollowResponse.ERROR
            return err

    def AcceptFollow(self, request, context):
        resp = follows_pb2.FollowResponse()
        if not request.handle or not request.follower.handle:
            self._logger.error('Error accepting follow: bad arguments')
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = 'Could not accept follow.'
            return resp

        follower, followed = self._get_users(resp, request)
        if follower is None or followed is None:
            return resp

        err = self._get_follow(resp, follower.global_id, followed.global_id)
        if err is not None:
            return resp

        if request.follower.host:
            # Acceptor handles everything from here
            self._util.attempt_to_accept(followed, follower, self._host_name,
                                         request.is_accepted)

        self._modify_follow(resp, follower.global_id, followed.global_id,
                            request.is_accepted)
        return resp
