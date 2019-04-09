import os
import sys

from services.proto import delete_pb2 as dpb
from utils.articles import delete_article

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
        # TODO(CianLR): Check for people who announced the article and send
        # Announce Undos to their followers.
        if not delete_article(self._logger, self._db, ap_id=req.ap_id):
            return dpb.DeleteResponse(
                result_type=dpb.DeleteResponse.ERROR,
                error="Could not delete article",
            )
        return dpb.DeleteResponse(result_type=dpb.DeleteResponse.OK)

