from proto import article_pb2
from proto import database_pb2


class NewArticleServicer:

    def __init__(self, db_stub, logger):
        self._db_stub = db_stub
        self._logger = logger

    def send_insert_request(self, req, global_id):
        pe = database_pb2.PostsEntry(
            author=req.author,
            title=req.title,
            body=req.body,
            creation_datetime=req.creation_datetime,
            global_id= global_id
        )
        pr = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.INSERT,
            entry=pe
        )
        posts_response = self._db_stub.Posts(pr)

        return posts_response.result_type

    def CreateNewArticle(self, request, context):
        self._logger.info('Recieved a new article.')
        global_id = request.title + str(request.creation_datetime.seconds)
        success = self.send_insert_request(request, global_id)

        resp = article_pb2.NewArticleResponse()
        resp.global_id = global_id
        if success:
            resp.result_type = article_pb2.NewArticleResponse.OK
        else:
            resp.result_type = article_pb2.NewArticleResponse.ERROR
        return resp
