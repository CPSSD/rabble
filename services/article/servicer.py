from new_article_servicer import NewArticleServicer

from proto import article_pb2_grpc


class ArticleServicer(article_pb2_grpc.ArticleServicer):

    def __init__(self, db_stub, logger):
        self._logger = logger
        self._db_stub = db_stub

        new_article_servicer = NewArticleServicer(db_stub, logger)
        self.CreateNewArticle = new_article_servicer.CreateNewArticle
