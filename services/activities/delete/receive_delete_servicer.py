import os
import sys

from services.proto import delete_pb2 as dpb
from utils.articles import delete_article, get_article, get_sharers_of_article

HOSTNAME_ENV = 'HOST_NAME'

class ReceiveDeleteServicer:
    def __init__(self, logger, db, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get(HOSTNAME_ENV)
        if not self._hostname:
            self._logger.error("Hostname for SendDeleteServicer not set")
            sys.exit(1)

    def ReceiveDeleteActivity(self, req, ctx):
        self._logger.info("Received delete for article '%s'", req.ap_id)
        article = get_article(self._logger, self._db, ap_id=req.ap_id)
        if article is None:
            # Don't have the article, our work here is done.
            # This can happen for natural reasons, dublicate deletes,
            # deletes of articles that were created before a follower
            # followed the creator, etc.
            self._logger.info("Don't have article %s, exiting", req.ap_id)
            return dpb.DeleteResponse(result_type=dpb.DeleteResponse.OK)
        author = self._users_util.get_user_from_db(global_id=article.author_id)
        if author is None:
            return dpb.DeleteResponse(
                result_type=dpb.DeleteResponse.ERROR,
                error="Could not retrieve author",
            )
        # Grab the people who shared the article before we delete everything.
        sharer_ids = get_sharers_of_article(
            self._logger, self._db, article.global_id)
        # Delete the local copy.
        if not delete_article(self._logger, self._db, ap_id=req.ap_id):
            return dpb.DeleteResponse(
                result_type=dpb.DeleteResponse.ERROR,
                error="Could not delete article",
            )
        # Forward the delete to the announcers.
        delete_obj = self._activ_util.build_delete(
            author, article, self._hostname)
        for user_id in sharer_ids:
            err = self._activ_util.forward_activity_to_followers(
                user_id, delete_obj)
            if err is not None:
                # Warn but do not quit on error sending to announcer followers.
                self._logger.warning(
                    "Sending activity to %d followers failed", user_id)
        return dpb.DeleteResponse(result_type=dpb.DeleteResponse.OK)

