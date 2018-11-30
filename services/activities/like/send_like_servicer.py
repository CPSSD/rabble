import json
from urllib import request

from services.proto import database_pb2
from services.proto import like_pb2

class SendLikeServicer:
    def __init__(self, logger, db, user_util, activ_util):
        self._logger = logger
        self._db = db
        self._user_util = user_util
        self._activ_util = activ_util

    def _build_activity(self, like_actor, liked_object):
        return {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': 'Like',
            'actor': like_actor,
            'object': liked_object,
        }

    def _create_article_object(self, article):
        return {
            'id': article.id,
        }

    def _create_actor_object(self, liker_host, liker_handle):
        return {
            'host': liker_host,
            'handle': liker_handle,
        }

    def _get_author_inbox(self, article):
        user = self._user_utils.get_user_from_db(
            global_id=article.author_id)
        if user is None:
            return None
        if user.host is None:
            #TODO(CianLR): Handle local users.
            return 'Oh fuck'
        return self._activ_util.build_inbox_url(user.handle, user.host)

    def _get_article(self, article_id):
        req = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.FIND,
            match=database_pb2.PostsEntry(
                global_id=article_id,
            ),
        )
        self._logger.info("Sending request to DB for article %d", article_id)
        resp = self._db.Posts(req)
        if resp.result_type == database_pb2.PostsResponse.ERROR:
            return None, resp.error
        elif len(resp.results) != 1:
            return None, "Expected 1 result, got " + str(len(resp.results))
        return resp.results[0], None
    
    def SendLikeActivity(self, req, context):
        response = like_pb2.LikeResponse(
            result_type=like_pb2.LikeResponse.OK)
        # Get article from DB
        article, err = self._get_article(req.article_id)
        if err is not None:
            self._logger.error("Error getting article: " + err)
            response.result_type = like_pb2.LikeResponse.ERROR
            response.error = err
            return response
        activity = self._build_activity(
            self._create_actor_object(req.liker_host, req.liker_handle),
            self._create_article_object(article))
        resp, err = self._activ_util.send_activity(
            activity, self._get_author_inbox(article))
        if err is not None:
            response.result_type = like_pb2.LikeResponse.ERROR
            response.error = err
        return response
 

