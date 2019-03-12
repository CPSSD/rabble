from services.proto import database_pb2
from services.proto import users_pb2

class GetCssHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db = db_stub

    def GetCss(self, request, context):
        self._logger.info("Request to get the CSS for user %s",
                          request.handle)
        resp = self._db.Users(database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            match=database_pb2.UsersEntry(
                handle=request.handle,
                host_is_null=True,
            )
        ))
        if resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.error("Error getting CSS: %s", resp.error)
            return users_pb2.GetCssResponse(
                result=users_pb2.GetCssResponse.ERROR,
                error=resp.error,
            )
        elif len(resp.results) != 1:
            self._logger.error(
                "Got wrong number of results, expected 1 got %d",
                len(resp.results))
            return users_pb2.GetCssResponse(
                result=users_pb2.GetCssResponse.ERROR,
                error="Got wrong number of results",
            )
        return users_pb2.GetCssResponse(
            result=users_pb2.GetCssResponse.OK,
            css=resp.results[0].post_title_css,
        )

