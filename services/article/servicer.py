from new_article_servicer import NewArticleServicer

import article_pb2_grpc


class ArticleServicer(article_pb2_grpc.ArticleServicer):

    def __init__(self, logger):
        self._logger = logger

        new_article_servicer = NewArticleServicer(logger)
        self.RecieveNewArticle = new_article_servicer.RecieveNewArticle
