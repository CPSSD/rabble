import os

from services.proto import database_pb2 as db_pb
from services.proto import like_pb2
from like_util import build_like_activity


class ReceiveLikeServicer:
    def __init__(self, logger, db, user_util, activ_util, hostname=None):
        self._logger = logger
        self._db = db
        self._user_util = user_util
        self._activ_util = activ_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get('HOST_NAME')
        if not self._hostname:
            self._logger.error("'HOST_NAME' env var is not set")
            sys.exit(1)

    def _get_liking_user(self, liker_id):
        host, handle = self._user_util.parse_actor(liker_id)
        # Sets the host to None if the user is local.
        host = self._activ_util.get_host_name_param(host, self._hostname)
        user = self._user_util.get_or_create_user_from_db(
            handle=handle, host=host, host_is_null=(host is None))
        return user.global_id if user else None

    def _add_like_to_db(self, user_id, article_id):
        req = db_pb.LikeEntry(
            user_id=user_id,
            article_id=article_id,
        )
        resp = self._db.AddLike(req)
        if resp.result_type != db_pb.DBLikeResponse.OK:
            return resp.error
        return None

    def _forward_like(self, author_id, req):
        # Forward like to following servers.
        self._logger.info("Sending like to followers")
        resp = self._db.Follow(db_pb.DbFollowRequest(
            request_type=db_pb.DbFollowRequest.FIND,
            match=db_pb.Follow(followed=author_id),
        ))
        if resp.result_type != db_pb.DbFollowResponse.OK:
            return db_pb.error
        self._logger.info("Have %d users to notify", len(resp.results))
        # Gather up the users, filter local and non-unique hosts.
        hosts_to_users = {}
        for follow in resp.results:
            user = self._user_util.get_user_from_db(
                global_id=follow.follower)
            if user is None:
                self._logger.warning(
                    "Could not find user %d, skipping", user_id)
                continue
            elif not user.host:
                continue  # Local user, already handled.
            hosts_to_users[user.host] = user
        # Send the activities off.
        activity = build_like_activity(req.liker_id, req.liked_object)
        for host, user in hosts_to_users.items():
            inbox = self._activ_util.build_inbox_url(user.handle, host)
            self._logger.info("Sending like to: %s", inbox)
            resp, err = self._activ_util.send_activity(activity, inbox)
            if err:
                self._logger.warning(
                    "Error sending activity to '%s' at '%s': %s",
                    user.handle, host, str(err)
                )
        return None

    def ReceiveLikeActivity(self, req, context):
        self._logger.debug("Got like for %s from %s",
                           req.liked_object,
                           req.liker_id)
        # Get article.
        article, err = self._activ_util.get_article_by_ap_id(req.liked_object)
        if err is not None:
            self._logger.error("Error getting article: %s", err)
            return like_pb2.LikeResponse(
                result_type=like_pb2.LikeResponse.ERROR,
                error=err,
            )
        # Get user.
        user_id = self._get_liking_user(req.liker_id)
        if user_id is None:
            self._logger.error("Could not get liking user")
            return like_pb2.LikeResponse(
                result_type=like_pb2.LikeResponse.ERROR,
                error="Could not get liking user",
            )
        # Add like to local database.
        err = self._add_like_to_db(user_id, article.global_id)
        if err is not None:
            self._logger.error("Could not add like to DB: %s", err)
            return like_pb2.LikeResponse(
                result_type=like_pb2.LikeResponse.ERROR,
                error="Could not add like to DB: " + err
            )
        if self._user_util.user_is_local(article.author_id):
            # This is the author's local server, must distribute like to
            # all the servers who follow this user.
            self._activ_util.forward_activity_to_followers(
                article.author_id,
                build_like_activity(req.liker_id, req.liked_object))
        return like_pb2.LikeResponse(
            result_type=like_pb2.LikeResponse.OK
        )
