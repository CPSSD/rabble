from services.proto import delete_pb2 as dpb

class SendLikeDeleteServicer:
    def __init__(self, logger, db, activ_util):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util

    def SendLikeDeleteActivity(self, req, ctx):
        self._logger.info(
            "Got request to delete like for article {} by user {}".format(
                req.article_id, req.liker_handle))
        return dpb.DeleteResponse()

