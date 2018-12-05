from services.proto import database_pb2 as db_pb
from services.proto import like_pb2

class ReceiveLikeServicer:
    def __init__(self, logger, db, user_util):
        self._logger = logger
        self._db = db
        self._user_util = user_util

    def _get_liked_object(self, liked_obj):
        # Case one, foreign article.
        posts_req = db_pb.PostsRequest(
            request_type=db_pb.PostsRequest.FIND,
            match=db_pb.PostsEntry(
                ap_id=liked_obj,
            ),
        )
        resp = self._db.Posts(posts_req)
        if resp.result_type != db_pb.PostsResponse.OK:
            return None, resp.error
        elif len(resp.results) > 1:
            return None, "Recieved too many results from DB"
        elif len(resp.results) == 1:
            return resp.results[0].global_id, None
        # Case two, local article
        


    def ReceiveLikeActivity(self, req, context):
        self._logger.debug("Got like for %s from %s",
                           req.liked_object,
                           req.liker_id)
        return like_pb2.LikeResponse(
            result_type=like_pb2.LikeResponse.ERROR,
            error="Not implemented",
        )

