import os
import sys

from services.proto import database_pb2 as dbpb
from services.proto import update_pb2 as upb
from utils.articles import get_article, convert_to_tags_string, md_to_html

HOSTNAME_ENV = 'HOST_NAME'


class SendUpdateServicer:
    def __init__(self, logger, db, md, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._md = md
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get(HOSTNAME_ENV)
        if not self._hostname:
            self._logger.error("Hostname for SendUpdateServicer not set")
            sys.exit(1)

    def _update_locally(self, article, req):
        self._logger.info("Sending update request to DB")
        html_body = md_to_html(self._md, req.body)
        resp = self._db.Posts(dbpb.PostsRequest(
            request_type=dbpb.PostsRequest.UPDATE,
            match=dbpb.PostsEntry(global_id=article.global_id),
            entry=dbpb.PostsEntry(
                title=req.title,
                body=html_body,
                md_body=req.body,
                tags=convert_to_tags_string(req.tags),
                summary=req.summary,
            ),
        ))
        if resp.result_type != dbpb.PostsResponse.OK:
            self._logger.error("Could not update article: %s", resp.error)
            return False
        return True

    def _build_update(self, user, article, req):
        actor = self._activ_util.build_actor(user.handle, self._hostname)
        article_url = self._activ_util.build_article_url(article)
        timestamp = article.creation_datetime.ToJsonString()
        ap_article = self._activ_util.build_article(
            article.ap_id,
            req.title,
            timestamp,
            actor,
            req.body,
            req.summary,
            article_url=article_url,
        )
        return {
            "@context": self._activ_util.rabble_context(),
            "type": "Update",
            "object": ap_article,
        }

    def SendUpdateActivity(self, req, ctx):
        self._logger.info("Got request to update article %d from %d",
                          req.article_id, req.user_id)
        user = self._users_util.get_user_from_db(global_id=req.user_id)
        if user is None:
            return upb.UpdateResponse(
                result_type=upb.UpdateResponse.ERROR,
                error="Error retrieving user",
            )
        article = get_article(self._logger, self._db, global_id=req.article_id)
        if article is None:
            return upb.UpdateResponse(
                result_type=upb.UpdateResponse.ERROR,
                error="Error retrieving article",
            )
        if article.author_id != user.global_id:
            self._logger.warning(
                "User %d requested to edit article belonging to user %d",
                req.user_id, article.author_id)
            return upb.UpdateResponse(result_type=upb.UpdateResponse.DENIED)
        # Update article locally
        if not self._update_locally(article, req):
            return upb.UpdateResponse(
                result_type=upb.UpdateResponse.ERROR,
                error="Error updating article",
            )
        # Send out update activity
        update_obj = self._build_update(user, article, req)
        self._logger.info("Activity: %s", str(update_obj))
        err = self._activ_util.forward_activity_to_followers(
            req.user_id, update_obj)
        if err is not None:
            return upb.UpdateResponse(
                result_type=upb.UpdateResponse.ERROR,
                error=err,
            )
        return upb.UpdateResponse(result_type=upb.UpdateResponse.OK)
