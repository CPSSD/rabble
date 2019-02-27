import os
import sys

from activities.like import like_util
from services.proto import database_pb2 as dbpb
from services.proto import delete_pb2 as dpb

class SendLikeDeleteServicer:
    def __init__(self, logger, db, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get('HOST_NAME')
        if not self._hostname:
            self._logger.error("'HOST_NAME env var not set")
            sys.exit(1)

    def _get_article(self, article_id):
        posts_req = dbpb.PostsRequest(
            request_type=dbpb.PostsRequest.FIND,
            match=dbpb.PostsEntry(
                global_id=article_id,
            ),
        )
        find_resp = self._db.Posts(posts_req)
        if find_resp.result_type != dbpb.PostsResponse.OK:
            return None, find_resp.error
        elif len(find_resp.results) != 1:
            return None, "Expecting 1 result, got {}".format(
                len(find_resp.results))
        return find_resp.results[0], None

    def _get_user(self, global_id):
        user = self._users_util.get_user_from_db(global_id=global_id)
        if user is None:
            return None, "Error getting user"
        if not user.host:
            user.host = self._hostname
        return user, None

    def _build_delete_object(self, user_handle, author, article):
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Delete",
            "object": like_util.build_like_activity(
                self._activ_util.build_actor(user_handle, self._hostname),
                self._activ_util.build_article(author, article)),
        }, None

    def _build_error_response(self, err):
        return dpb.DeleteResponse(
            result_type=dpb.DeleteResponse.ERROR,
            error=err,
        )

    def SendLikeDeleteActivity(self, req, ctx):
        self._logger.info(
            "Got request to delete like for article {} by user {}".format(
                req.article_id, req.liker_handle))
        article, err = self._get_article(req.article_id)
        if err is not None:
            return self._build_error_response(err)
        author, err = self._get_user(article.author_id)
        if err is not None:
            return self._build_error_response(err)
        delete_obj, err = self._build_delete_object(
            req.liker_handle, author, article)
        if err is not None:
            return self._build_error_response(err)
        inbox = self._activ_util.build_inbox_url(author.handle, author.host)
        _, err = self._activ_util.send_activity(delete_obj, inbox)
        if err is not None:
            return self._build_error_response(err)
        return dpb.DeleteResponse(result_type=dpb.DeleteResponse.OK)

