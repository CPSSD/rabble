from proto import article_pb2
from proto import database_pb2
from proto import mdc_pb2


class PreviewServicer:

    def __init__(self, md_stub, logger):
        self._md_stub = md_stub
        self._logger = logger

    def get_html_body(self, body):
        convert_req = mdc_pb2.MDRequest(md_body=body)
        res = self._md_stub.MarkdownToHTML(convert_req)
        return res.html_body

    def PreviewArticle(self, req, context):
        self._logger.info('Recieved a new article to Preview.')
        html_body = self.get_html_body(req.body)
        na = article_pb2.NewArticle(
            author=req.author,
            title=req.title,
            body=html_body,
            creation_datetime=req.creation_datetime
        )
        resp = article_pb2.PreviewResponse(
            preview=na,
            result_type=article_pb2.NewArticleResponse.OK
        )
        return resp
