from services.proto import article_pb2
from services.proto import database_pb2
from services.proto import create_pb2
from services.proto import mdc_pb2

from utils import posts


class NewArticleServicer:

    def __init__(self, create_stub, db_stub, md_stub, search_stub, logger, users_util):
        self._create_stub = create_stub
        self._db_stub = db_stub
        self._md_stub = md_stub
        self._search_stub = search_stub
        self._logger = logger
        self._users_util = users_util

    def get_html_body(self, body):
        convert_req = mdc_pb2.MDRequest(md_body=body)
        res = self._md_stub.MarkdownToHTML(convert_req)
        return res.html_body

    def send_insert_request(self, req):
        author = self._users_util.get_user_from_db(handle=req.author,
                                                   host=None)
        if author is None:
            self._logger.error('Could not find user in db: ' + str(req.author))
            return database_pb2.PostsResponse.error, None
        html_body = self.get_html_body(req.body)
        pe = database_pb2.PostsEntry(
            author_id=author.global_id,
            title=req.title,
            body=html_body,
            md_body=req.body,
            creation_datetime=req.creation_datetime,
            ap_id=req.ap_id,
        )
        pr = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.INSERT,
            entry=pe
        )
        posts_resp = self._db_stub.Posts(pr)
        if posts_resp.result_type == database_pb2.PostsResponse.ERROR:
            self._logger.error('Could not insert into db: %s', posts_resp.error)

        pe.global_id = posts_resp.global_id
        posts.index(self._logger, self._search_stub, pe)

        return posts_resp.result_type, posts_resp.global_id

    def send_create_activity_request(self, req, global_id):
        html_body = self.get_html_body(req.body)
        ad = create_pb2.ArticleDetails(
            author=req.author,
            title=req.title,
            body=html_body,
            md_body=req.body,
            creation_datetime=req.creation_datetime,
            global_id=global_id,
        )
        create_resp = self._create_stub.SendCreate(ad)

        return create_resp.result_type

    def CreateNewArticle(self, req, context):
        self._logger.info('Recieved a new article.')
        success, global_id = self.send_insert_request(req)

        resp = article_pb2.NewArticleResponse()
        if success == database_pb2.PostsResponse.OK:
            self._logger.info('Article created.')
            resp.result_type = article_pb2.NewArticleResponse.OK
            if not req.foreign:
                # TODO (sailslick) persist create activities
                # or add to queueing service
                create_success = self.send_create_activity_request(
                    req, global_id)
                if create_success == create_pb2.CreateResponse.ERROR:
                    self._logger.error('Could not send create Activity')
        else:
            resp.result_type = article_pb2.NewArticleResponse.ERROR
        return resp
