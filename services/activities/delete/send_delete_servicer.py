import os
import sys

from services.proto import database_pb2 as dbpb
from services.proto import delete_pb2 as dpb
from utils.articles import get_article, delete_article, get_sharers_of_article

HOSTNAME_ENV = 'HOST_NAME'


class SendDeleteServicer:
    def __init__(self, logger, db, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get(HOSTNAME_ENV)
        if not self._hostname:
            self._logger.error("Hostname for SendDeleteServicer not set")
            sys.exit(1)

    def SendDeleteActivity(self, req, ctx):
        self._logger.info("Got request to delete article %d from %d",
                          req.article_id, req.user_id)
        user = self._users_util.get_user_from_db(global_id=req.user_id)
        if user is None:
            return dpb.DeleteResponse(
                result_type=dpb.DeleteResponse.ERROR,
                error="Could not retrieve user",
            )
        article = get_article(self._logger, self._db, global_id=req.article_id)
        if article is None:
            return dbp.DeleteResponse(
                result_type=dpb.DeleteResponse.ERROR,
                error="Could not retrieve article",
            )
        if article.author_id != req.user_id:
            self._logger.error("User requesting article deletion isn't author")
            return dbp.DeleteResponse(
                result_type=dpb.DeleteResponse.DENIED,
                error="User is not the author of this article",
            )
        sharer_ids = get_sharers_of_article(
            self._logger, self._db, article.global_id)
        if not delete_article(self._logger, self._db, global_id=article.global_id):
            return dpb.DeleteResponse(
                result_type=dpb.DeleteResponse.ERROR,
                error="Could not delete article locally",
            )
        delete_obj = self._activ_util.build_delete(user, article)
        self._logger.info("Activity: %s", str(delete_obj))
        err = self._activ_util.forward_activity_to_followers(
            req.user_id, delete_obj)
        if err is not None:
            return dpb.DeleteResponse(
                result_type=dpb.DeleteResponse.ERROR,
                error=err,
            )
        # Send deletes of the article to the followers of people who
        # announced the article. There may be some duplicate Deletes
        # sent but this is acceptable.
        # This roughly the same pattern Mastodon follows:
        # https://github.com/tootsuite/mastodon/issues/5761#issuecomment-345875480
        for user_id in sharer_ids:
            err = self._activ_util.forward_activity_to_followers(
                user_id, delete_obj)
            if err is not None:
                # Warn but do not quit on error sending to announcer followers.
                self._logger.warning(
                    "Sending activity to %d followers failed", user_id)
        self._logger.info("Article %d successfully deleted", req.article_id)
        return dpb.DeleteResponse(result_type=dpb.DeleteResponse.OK)

