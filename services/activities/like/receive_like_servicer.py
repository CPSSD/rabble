import os

from services.proto import database_pb2 as db_pb
from services.proto import like_pb2
from services.proto import recommend_posts_pb2
from like_util import build_like_activity


class ReceiveLikeServicer:
    def __init__(self, logger, db, user_util, activ_util, post_recommendation_stub=None, hostname=None):
        self._logger = logger
        self._db = db
        self._user_util = user_util
        self._activ_util = activ_util
        self._post_recommendation_stub = post_recommendation_stub
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

    def _add_like_to_user_model(self, user_id, article_id):
        req = db_pb.LikeEntry(
            user_id=user_id,
            article_id=article_id,
        )
        resp = self._post_recommendation_stub.UpdateModel(req)
        if resp.result_type != recommend_posts_pb2.PostRecommendationsResponse.OK:
            self._logger.error(
                "UpdateModel for post recommendation failed: %s", resp.message)

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

            # If post_recommender is on, send like to post_recommender
            if self._post_recommendation_stub is not None:
                self._add_like_to_user_model(user_id, article.global_id)

        return like_pb2.LikeResponse(
            result_type=like_pb2.LikeResponse.OK
        )
