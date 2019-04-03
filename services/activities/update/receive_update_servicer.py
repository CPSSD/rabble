import os
import sys

from services.proto import database_pb2 as dbpb
from services.proto import update_pb2 as upb
from utils.articles import md_to_html

HOSTNAME_ENV = 'HOST_NAME'

class ReceiveUpdateServicer:
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

    def ReceiveUpdateActivity(self, req, ctx):
        self._logger.info("Received edit for article '%s'", req.title)
        html_body = md_to_html(self._md, req.body)
        resp = self._db.Posts(dbpb.PostsRequest(
            request_type=dbpb.PostsRequest.UPDATE,
            match=dbpb.PostsEntry(ap_id=req.ap_id),
            entry=dbpb.PostsEntry(
                title=req.title,
                body=html_body,
                md_body=req.body,
                summary=req.summary,
            ),
        ))
        if resp.result_type != dbpb.PostsResponse.OK:
            self._logger.error("Could not update article: %s", resp.error)
            return upb.UpdateResponse(
                result_type=upb.UpdateRespones.ERROR,
                error="Error updating article in DB",
            )
        return upb.UpdateResponse(result_type=upb.UpdateResponse.OK)

