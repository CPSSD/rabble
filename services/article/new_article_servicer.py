from proto import article_pb2
from proto import database_pb2
from proto import create_pb2


class NewArticleServicer:

    def __init__(self, create_stub, db_stub, logger, users_util):
        self._create_stub = create_stub
        self._db_stub = db_stub
        self._logger = logger
        self._users_util = users_util

    def send_insert_request(self, req):
        author = self._users_util.get_user_from_db(handle=req.author,
                                                   host=None)
        if author is None:
            self._logger.error('Could not find user in db: ' + str(req.author))
            return database_pb2.PostsResponse.error
        pe = database_pb2.PostsEntry(
            author_id=author.global_id,
            title=req.title,
            body=req.body,
            creation_datetime=req.creation_datetime
        )
        pr = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.INSERT,
            entry=pe
        )
        posts_resp = self._db_stub.Posts(pr)
        if posts_resp.result_type == database_pb2.PostsResponse.ERROR:
            self._logger.error('Could not insert into db: %s', posts_resp.error)

        return posts_resp.result_type

    def send_create_activity_request(self, req):
        ad = create_pb2.ArticleDetails(
            author=req.author,
            title=req.title,
            body=req.body,
            creation_datetime=req.creation_datetime
        )
        create_resp = self._create_stub.SendCreate(ad)

        return create_resp.result_type

    def CreateNewArticle(self, req, context):
        self._logger.info('Recieved a new article.')
        success = self.send_insert_request(req)

        resp = article_pb2.NewArticleResponse()
        if success == database_pb2.PostsResponse.OK:
            resp.result_type = article_pb2.NewArticleResponse.OK
            create_success = self.send_create_activity_request(req)
        else:
            resp.result_type = article_pb2.NewArticleResponse.ERROR
        return resp
