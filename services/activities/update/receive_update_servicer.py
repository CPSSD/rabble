import os
import sys

from services.proto import database_pb2 as dbpb
from services.proto import update_pb2 as upb

HOSTNAME_ENV = 'HOST_NAME'

class ReceiveUpdateServicer:
    def __init__(self, logger, db, activ_util, users_util, hostname=None):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._users_util = users_util
        self._hostname = hostname if hostname else os.environ.get(HOSTNAME_ENV)
        if not self._hostname:
            self._logger.error("Hostname for SendUpdateServicer not set")
            sys.exit(1)

    def ReceiveUpdateActivity(self, req, ctx):
        return upb.UpdateResponse(result_type=upb.UpdateResponse.OK)

