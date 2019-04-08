import os
import sys

from services.proto import database_pb2 as dbpb
from services.proto import delete_pb2 as dpb
from utils.articles import get_article

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
        return dpb.DeleteResponse(result_type=dpb.DeleteResponse.OK)
