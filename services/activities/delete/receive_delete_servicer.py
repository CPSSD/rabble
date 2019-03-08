import os
import sys

from services.proto import database_pb2 as dbpb
from services.proto import delete_pb2 as dpb

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

    def match_hostname(self, host):
        if host is None:
            return None
        # Chop off protocol, works if no protocol too.
        foreign_host = host.split('://')[-1]
        local_host = self._hostname.split('://')[-1]
        if foreign_host == local_host:
            return None
        return foreign_host

    def gen_error(self, err):
        return dpb.DeleteResponse(
            result_type=dpb.DeleteResponse.ERROR,
            error=err,
        )

    def get_user(self, user_ap):
        host, handle = self._users_util.parse_actor(user_ap)
        host = self.match_hostname(host)
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

    def get_article(self, article_ap):
        posts_req = dbpb.PostsRequest(
            request_type=dbpb.PostsRequest.FIND,
            match=dbpb.PostsEntry(
                ap_id=article_ap,
            ),
        )
        resp = self._db.Posts(posts_req)
        if resp.result_type != dbpb.PostsResponse.OK:
            self._logger.error("Error from DB: " + resp.error)
            return None
        elif len(resp.results) > 1:
            self._logger.error(
                "Got too many results for article query ({})".format(
                    str(len(resp.results))))
            return None
        elif len(resp.results) == 0:
            self._logger.error("Got no results for article query")
            return None
        return resp.results[0]

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
        article = self.get_article(req.liked_object_ap_id)
        if article is None:
            return self.gen_error("Could not get article: " +
                                  req.liked_object_ap_id)
        if not self.remove_like_from_db(user.global_id, article.global_id):
            return self.gen_error("Error removing like from DB")
        # TODO(CianLR): If this is the author's local server then federate
        # the unlike
        return dpb.DeleteResponse(
            result_type=dpb.DeleteResponse.OK,
        )

