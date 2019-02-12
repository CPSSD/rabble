from new_article_servicer import NewArticleServicer
from preview_servicer import PreviewServicer

from services.proto import article_pb2_grpc


class ArticleServicer(article_pb2_grpc.ArticleServicer):

    def __init__(self, create_stub, db_stub, md_stub, search_stub, logger, users_util):
        self._logger = logger
        self._create_stub = create_stub
        self._db_stub = db_stub
        self._md_stub = md_stub
        self._users_util = users_util
        self._search_stub = search_stub

        new_article_servicer = NewArticleServicer(create_stub, db_stub,
                                                  md_stub, search_stub,
                                                  logger, users_util)
        self.CreateNewArticle = new_article_servicer.CreateNewArticle
        preview_servicer = PreviewServicer(md_stub, logger)
        self.PreviewArticle = preview_servicer.PreviewArticle
