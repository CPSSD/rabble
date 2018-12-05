import os

from services.proto import database_pb2 as db_pb
from services.proto import like_pb2

class ReceiveLikeServicer:
    def __init__(self, logger, db, user_util, hostname=None):
        self._logger = logger
        self._db = db
        self._user_util = user_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get('HOST_NAME')
        if not self._hostname:
            self._logger.error("'HOST_NAME' env var is not set")
            sys.exit(1)

    def _get_host_name_param(self, host):
        # Remove protcol
        foreign_host = host.split('://')[-1]
        local_host = self._hostname.split('://')[-1]
        if foreign_host == local_host:
            return None
        return host

    def _get_liking_user(self, liker_id):
        host, handle = self._user_util.parse_actor(liker_id)
        # Sets the host to None if the user is local.
        host = self._get_host_name_param(host)
        user = self._user_util.get_or_create_user_from_db(
            handle=handle, host=host)
        return user.global_id if user else None

    def _get_liked_article(self, liked_obj):
        # Case one, foreign article.
        posts_req = db_pb.PostsRequest(
            request_type=db_pb.PostsRequest.FIND,
            match=db_pb.PostsEntry(
                ap_id=liked_obj,
            ),
        )
        resp = self._db.Posts(posts_req)
        if resp.result_type != db_pb.PostsResponse.OK:
            return None, resp.error
        elif len(resp.results) > 1:
            return None, "Recieved too many results from DB"
        elif len(resp.results) == 0:
            # NOTE: This can happen natually.
            # cian@a.com follows ross@b.org.
            # b.org sends a Like for an article by ross that already existed.
            # a.com didn't get the original Create so it can't find it.
            return None, "No matching DB entry for this article"
        return resp.results[0], None

    def _add_like_to_db(self, user_id, article_id):
        req = db_pb.LikeEntry(
            user_id=user_id,
            article_id=article_id,
        )
        resp = self._db.AddLike(req)
        if resp.result_type != db_pb.AddLikeResponse.OK:
            return resp.error
        return None

    def _user_is_local(self, user_id):
        user = self._user_util.get_user_from_db(global_id=user_id)
        if user is None:
            self._logger.error(
                "Could not get author from DB, "
                "assuming they're foreign and continuing"
            )
            return False
        # Host is empty if user is local.
        return user.host == ""

    def _forward_like(self, author_id, req):
        # TODO(CianLR): Forward like to following servers.
        pass

    def ReceiveLikeActivity(self, req, context):
        self._logger.debug("Got like for %s from %s",
                           req.liked_object,
                           req.liker_id)
        # Get article.
        article, err = self._get_liked_article(req.liked_object)
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
        if self._user_is_local(article.author_id):
            # This is the author's local server, must distribute like to
            # all the servers who follow this user.
            self._forward_like(article.author_id, req)
        return like_pb2.LikeResponse(
            result_type=like_pb2.LikeResponse.OK
        )

