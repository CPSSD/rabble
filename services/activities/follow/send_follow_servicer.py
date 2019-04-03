import json

from services.proto import s2s_follow_pb2, database_pb2


class SendFollowServicer:

    def __init__(self, logger, activ_util, db_stub):
        self._logger = logger
        self._activ_util = activ_util
        self._db = db_stub

    def _build_activity(self, follower_actor, followed_actor, sendable=True):
        '''Build a follow activity for actor `follower_actor` following
        actor `followed_actor`.

        If `sendable` is set to True, this function will add the extra fields to
        the JSON to turn it into a proper fully qualified and ready-to-send
        Activity (ie. the context, `to` field, etc).
        If `sendable` is not True, then it will generate an Activity that can
        be embedded in another one (ie. an Undo).'''
        d = {
            'type': 'Follow',
            'actor': follower_actor,
            'object': followed_actor,
        }
        if sendable:
            d['@context'] = self._activ_util.rabble_context()
            d['to'] = [followed_actor]
        return d


    def _build_undo(self, undoer_actor, unfollowed_actor, follow_activity):
        # TODO(CianLR): Replace 'Delete' here with 'Undo'.
        d = {
            '@context':  self._activ_util.rabble_context(),
            'type': 'Delete',
            'actor': undoer_actor,
            'object': follow_activity,
            'to': [unfollowed_actor]
        }
        return d
      
    def _get_local_user_id(self, handle):
        user = database_pb2.UsersEntry(handle=handle, host_is_null=True)
        req = database_pb2.UsersRequest(request_type=database_pb2.UsersRequest.FIND,
                                        match=user)
        resp = self._db.Users(req)
        if resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.warning('Error getting user: {}'.format(resp.error))
            return None
        if not len(resp.results):
            self._logger.warning('Could not find user.')
            return None
        return resp.results[0].global_id

    def _send(self, activ, url, handle):
        sender_id = self._get_local_user_id(handle)
        resp, err = self._activ_util.send_activity(activ, url, sender_id=sender_id)
        if err is not None:
            return err
        elif resp.status_code != 200:
            return "Got http error {}".format(resp.status_code)
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
        self._logger.debug(str(activity))

        err = self._send(activity, inbox_url, req.follower.handle)
        if err is None:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK
        else:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.ERROR
            resp.error = err
        return resp

    def SendUnfollowActivity(self, req, context):
        resp = s2s_follow_pb2.FollowActivityResponse()

        follower_actor = self._activ_util.build_actor(
            req.follower.handle, req.follower.host)
        followed_actor = self._activ_util.build_actor(
            req.followed.handle, req.followed.host)

        # Build a follow activity, then wrap it in an Undo activity
        follow_activity = self._build_activity(follower_actor,
                                               followed_actor,
                                               sendable=False)
        undo_activity = self._build_undo(follower_actor,
                                         followed_actor,
                                         follow_activity)

        inbox_url = self._activ_util.build_inbox_url(
            req.followed.handle, req.followed.host)

        self._logger.debug('Sending unfollow activity to foreign server')
        self._logger.debug(str(undo_activity))
        sender_id = self._get_local_user_id(req.follower.handle)
        _, err = self._activ_util.send_activity(undo_activity,
                                                inbox_url,
                                                sender_id=sender_id)
        if err is None:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.OK
        else:
            resp.result_type = s2s_follow_pb2.FollowActivityResponse.ERROR
            resp.error = err


        return resp
