import os
import sys

from activities.like import like_util
from services.proto import database_pb2 as dbpb
from services.proto import undo_pb2 as upb

HOSTNAME_ENV = 'HOST_NAME'

class ReceiveLikeDeleteServicer:
    def __init__(self, logger, db, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get(HOSTNAME_ENV)
        if not self._hostname:
            self._logger.error("Hostname for SendLikeDeleteServicer not set")
            sys.exit(1)

    def gen_error(self, err):
        return upb.UndoResponse(
            result_type=upb.UndoResponse.ERROR,
            error=err,
        )

    def get_user(self, user_ap):
        host, handle = self._users_util.parse_actor(user_ap)
        host = self._activ_util.get_host_name_param(host, self._hostname)
        if handle is None:
            self._logger.error("Could not parse user: " + user_ap)
            return None
        user = self._users_util.get_user_from_db(handle=handle,
                                                 host=host,
                                                 host_is_null=(host is None))
        if user is None:
            self._logger.error("Could not get user {}@{} from db".format(
                handle, str(host)))
            return None
        return user

    def remove_like_from_db(self, user_id, article_id):
        req = dbpb.LikeEntry(
            user_id=user_id,
            article_id=article_id,
        )
        resp = self._db.RemoveLike(req)
        if resp.result_type != dbpb.DBLikeResponse.OK:
            self._logger.error("Error from DB: %s", resp.error)
            return False
        return True

    def ReceiveLikeDeleteActivity(self, req, ctx):
        self._logger.debug("Got delete for like object")
        user = self.get_user(req.liking_user_ap_id)
        if user is None:
            return self.gen_error("Couldn't get user: " +
                                  req.liking_user_ap_id)
        article, err = self._activ_util.get_article_by_ap_id(
            req.liked_object_ap_id)
        if err is not None:
            self._logger.error("Error getting article: %s", err)
            return self.gen_error("Could not get article: " +
                                  req.liked_object_ap_id)
        if not self.remove_like_from_db(user.global_id, article.global_id):
            return self.gen_error("Error removing like from DB")
        # TODO(CianLR): If this is the author's local server then federate
        # the unlike
        if self._users_util.user_is_local(article.author_id):
            # Build the activity.
            a = self._activ_util.build_delete(like_util.build_like_activity(
                req.liking_user_ap_id,
                req.liked_object_ap_id))
            # Forward it to the followers
            self._activ_util.forward_activity_to_followers(article.author_id, a)
        return upb.UndoResponse(
            result_type=upb.UndoResponse.OK,
        )

