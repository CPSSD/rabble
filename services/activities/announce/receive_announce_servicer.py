import os

from services.proto import database_pb2 as db_pb
from services.proto import announce_pb2


class ReceiveAnnounceServicer:
    def __init__(self, logger, db, user_util, activ_util, hostname=None):
        self._logger = logger
        self._db = db
        self._user_util = user_util
        self._activ_util = activ_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get('HOST_NAME')
        if not self._hostname:
            self._logger.error("'HOST_NAME' env var is not set and no hostname is passed in")
            sys.exit(1)

    def ReceiveAnnounceActivity(self, req, context):
        self._logger.debug("Got announce for %s from %s at %s",
                           req.announced_object,
                           req.announcer_id,
                           req.announce_time)
        response = announce_pb2.AnnounceResponse(
            result_type=announce_pb2.AnnounceResponse.OK)
        return response
