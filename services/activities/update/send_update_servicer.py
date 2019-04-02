import os
import sys

from services.proto import database_pb2 as dbpb
from services.proto import update_pb2 as upb
from util import get_post

HOSTNAME_ENV = 'HOST_NAME'

class SendUpdateServicer:
    def __init__(self, logger, db, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get(HOSTNAME_ENV)
        if not self._hostname:
            self._logger.error("Hostname for SendUpdateServicer not set")
            sys.exit(1)

    def SendUpdateActivity(self, req, ctx):
        self._logger.info("Got request to update article %d from %d", req.article_id, req.user_id)
        user = self._users_util.get_user_from_db(global_id=req.user_id)
        article = get_post(self._logger, self._db, req.article_id)
        if article.author_id != user.global_id:
            self._logger.warning(
                "User %d requested to edit article belonging to user %d",
                req.user_id, article.author_id)
            return upb.UpdateResponse(result_type=upb.UpdateResponse.DENIED)
        return upb.UpdateResponse(result_type=upb.UpdateResponse.OK)

