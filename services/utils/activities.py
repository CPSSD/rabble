import json
from urllib import request
from services.proto import database_pb2


class ActivitiesUtil:
    def __init__(self, logger, db):
        self._logger = logger
        self._db = db

    def build_actor(self, handle, host):
        s = f'{host}/ap/@{handle}'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def build_article_url(self, author, article):
        """
        author must be a UserEntry proto.
        article must be a PostEntry proto.
        """
        if article.ap_id:
            return article.ap_id
        # Local article, build ID manually
        s = f'{author.host}/ap/@{author.handle}/{article.global_id}'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def build_delete(self, obj):
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Delete",
            "object": obj
        }

    def build_inbox_url(self, handle, host):
        # TODO(CianLR): Remove dupe logic from here and UsersUtil.
        s = f'{host}/ap/@{handle}/inbox'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def send_activity(self, activity, target_inbox):
        body = json.dumps(activity).encode("utf-8")
        headers = {"Content-Type": "application/ld+json"}
        req = request.Request(target_inbox,
                              data=body,
                              headers=headers,
                              method='POST')
        self._logger.debug('Sending activity to foreign server: %s',
                           target_inbox)
        try:
            resp = request.urlopen(req)
        except Exception as e:
            self._logger.error('Error trying to send activity:' + str(e))
            return None, str(e)
        return resp, None

    def get_article_by_ap_id(self, obj_id):
        posts_req = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.FIND,
            match=database_pb2.PostsEntry(
                ap_id=obj_id,
            ),
        )
        resp = self._db.Posts(posts_req)
        if resp.result_type != database_pb2.PostsResponse.OK:
            return None, resp.error
        elif len(resp.results) > 1:
            return None, "Recieved too many results from DB"
        elif len(resp.results) == 0:
            # NOTE: This can happen natually.
            # cian@a.com follows ross@b.org.
            # b.org sends a Like for an article by ross that already existed.
            # a.com didn't get the original Create so it can't find it.
            return None, "No matching DB entry for this article"
        return resp.results[0], None
