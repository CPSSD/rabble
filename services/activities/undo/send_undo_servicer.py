import os
import sys

from activities.like import like_util
from services.proto import database_pb2 as dbpb
from services.proto import undo_pb2 as upb

HOSTNAME_ENV = 'HOST_NAME'

class SendUndoException(Exception):
    pass

class SendLikeUndoServicer:
    def __init__(self, logger, db, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get(HOSTNAME_ENV)
        if not self._hostname:
            self._logger.error("Hostname for SendLikeUndoServicer not set")
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
            raise SendUndoException(find_resp.error)
        elif len(find_resp.results) != 1:
            raise SendUndoException("Expecting 1 result, got {}".format(
                len(find_resp.results)))
        return find_resp.results[0]

    def _build_like_undo_object(self, user_handle, author, article):
        return self._activ_util.build_undo(
            like_util.build_like_activity(
                self._activ_util.build_actor(user_handle, self._hostname),
                self._activ_util.build_article_url(author, article)
            )
        )

    def _build_error_response(self, err):
        return upb.UndoResponse(
            result_type=upb.UndoResponse.ERROR,
            error=err,
        )

    def SendLikeUndoActivity(self, req, ctx):
        self._logger.info(
            "Got request to undo like for article {} by user {}".format(
                req.article_id, req.liker_handle))
        try:
            article = self._get_article(req.article_id)
            author = self._users_util.get_user_from_db(
                global_id=article.author_id)
            if author is None:
                raise SendUndoException("Error getting author")
            if not author.host:
                author.host = self._hostname
            undo_obj = self._build_like_undo_object(
                req.liker_handle, author, article)
            inbox = self._activ_util.build_inbox_url(author.handle, author.host)
            _, err = self._activ_util.send_activity(undo_obj, inbox)
            if err:
                raise SendUndoException(err)
        except SendUndoException as e:
            return upb.UndoResponse(
                result_type=upb.UndoResponse.ERROR,
                error=str(e)
            )
        return upb.UndoResponse(result_type=upb.UndoResponse.OK)

