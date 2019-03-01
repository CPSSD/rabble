import os
import sys
import json
from urllib import request

from services.proto import database_pb2
from services.proto import like_pb2
from like_util import build_like_activity

class SendLikeServicer:
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

    def _get_author(self, article):
        user = self._user_util.get_user_from_db(
            global_id=article.author_id)
        if user is None:
            return None
        if not user.host:
            # The author must be local.
            user.host = self._hostname
        return user

    def _get_article(self, article_id):
        req = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.FIND,
            match=database_pb2.PostsEntry(
                global_id=article_id,
            ),
        )
        self._logger.info("Sending request to DB for article %d", article_id)
        resp = self._db.Posts(req)
        if resp.result_type == database_pb2.PostsResponse.ERROR:
            return None, resp.error
        elif len(resp.results) != 1:
            return None, "Expected 1 result, got " + str(len(resp.results))
        return resp.results[0], None
    
    def SendLikeActivity(self, req, context):
        response = like_pb2.LikeResponse(
            result_type=like_pb2.LikeResponse.OK)
        # Get article from DB
        article, err = self._get_article(req.article_id)
        if err is not None:
            self._logger.error("Error getting article: " + err)
            response.result_type = like_pb2.LikeResponse.ERROR
            response.error = err
            return response
        author = self._get_author(article)
        if author is None:
            self._logger.error("Error getting article author from DB")
            response.result_type = like_pb2.LikeResponse.ERROR
            response.error = "Error getting article author from DB"
            return response
        activity = build_like_activity(
            self._activ_util.build_actor(req.liker_handle, self._hostname),
            self._activ_util.build_article_url(author, article))
        inbox = self._activ_util.build_inbox_url(author.handle, author.host)
        resp, err = self._activ_util.send_activity(activity, inbox)
        if err is not None:
            response.result_type = like_pb2.LikeResponse.ERROR
            response.error = err
        return response
 

