import article_pb2
import database_pb2
import database_pb2_grpc


class NewArticleServicer:

    def __init__(self, logger):
        self._logger = logger

    def RecieveNewArticle(self, request, context):
        self._logger.info('Recieved a new article.')
        resp = article_pb2.newArticleResponse()
        resp.result_type = article_pb2.newArticleResponse.OK
        return resp
