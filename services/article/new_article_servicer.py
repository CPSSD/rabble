from services.proto import article_pb2
from services.proto import database_pb2
from services.proto import create_pb2
from services.proto import mdc_pb2
from services.proto import search_pb2


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

    def convert_to_tags_string(self, tags_array):
        # Using | to separate tags. So url encode | character in tags
        tags_array = [x.replace("|", "%7C") for x in tags_array]
        return "|".join(tags_array)

    def index(self, post_entry):
        """
        index takes a post proto and indexes it in the search service/

        Arguments:
        - post_entry (database.PostsEntry): A proto representing the post.
          This should have a valid global_id field.
        """
        req = search_pb2.IndexRequest(post=post_entry)
        resp = self._search_stub.Index(req)

        if resp.error:
            self._logger.warning("Error indexing post: %s", resp.error)

        return resp.result_type == search_pb2.IndexResponse.ResultType.Value("OK")

    def send_insert_request(self, req):
        global_id = req.author_id
        if not req.foreign:
            author = self._users_util.get_user_from_db(handle=req.author,
                                                       host_is_null=True)
            if author is None:
                self._logger.error('Could not find user in db: ' + str(req.author))
                return database_pb2.PostsResponse.error, None
            global_id = author.global_id

        html_body = self.get_html_body(req.body)
        tags_string = self.convert_to_tags_string(req.tags)
        pe = database_pb2.PostsEntry(
            author_id=global_id,
            title=req.title,
            body=html_body,
            md_body=req.body,
            creation_datetime=req.creation_datetime,
            ap_id=req.ap_id,
            tags=tags_string,
        )
        pr = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.INSERT,
            entry=pe
        )
        posts_resp = self._db_stub.Posts(pr)
        if posts_resp.result_type == database_pb2.PostsResponse.ERROR:
            self._logger.error('Could not insert into db: %s', posts_resp.error)

        pe.global_id = posts_resp.global_id
        self.index(pe)

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
