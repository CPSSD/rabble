from proto import create_pb2
from proto import database_pb2
from proto import article_pb2


class ReceiveCreateServicer:

    def __init__(self, db_stub, article_stub, logger, users_util):
        self._db_stub = db_stub
        self._article_stub = article_stub
        self._logger = logger
        self._users_util = users_util

    def _get_actor_ids(self, author, follower):
        # parse_actor parses form host/@actor and returns (host, actor)
        author_user = self._users_util.parse_actor(author)
        follower_user = self._users_util.parse_actor(follower)

        author_entry = self._users_util.get_user_from_db(
            handle=author_user[1],
            host=author_user[0]
        )
        if author_entry is None:
            self._logger.error("Could not find foreign author in db")
            return None, None, None

        follower_entry = self._users_util.get_user_from_db(
            handle=follower_user[1]
        )
        if follower_entry is None:
            self._logger.error("Could not find local follower user in db")
            return None, None, None

        return author_entry.global_id, follower_entry.global_id, author_user[1]

    def _check_follow(self, foreign_id, local_user_id):
        self._logger.info("Checking follow for new foreign article")
        follow_entry = database_pb2.Follow(
            followed=foreign_id,
            follower=local_user_id
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry
        )
        follow_resp = self._db_stub.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error(
                "Check if user id: %s followed %s, returned error: %s",
                local_user_id,
                foreign_id,
                follow_resp.error
            )
            return False

        if len(follow_resp.results) != 1:
            self._logger.error("No record of follow for foreign article")
            return False

        return True

    def _add_to_posts_db(self, author_handle, req):
        self._logger.debug("Calling article service with new foreign article")
        # set flag in article service that is foreign (so no need to create service)
        # TODO(sailslick) Unstring foreign_id when pr #159 is merged
        na = article_pb2.NewArticle(
            author=author_handle,
            title=req.title,
            body=req.content,
            creation_datetime=req.published,
            foreign=True
        )
        article_resp = self._article_stub.CreateNewArticle(na)
        if article_resp.result_type == article_pb2.NewArticleResponse.ERROR:
            self._logger.error(
                "New foreign article creation returned error: %s",
                article_resp.error
            )
            return False
        return True

    def ReceiveCreate(self, req, context):
        self._logger.debug("Recieved a new create notification.")
        resp = create_pb2.CreateResponse()

        # get actor ids
        # TODO (sailslick) when author ids are sent from client instead of handles
        # Remove extra return variable author_handle
        author_id, follower_id, author_handle = self._get_actor_ids(req.attributedTo, req.recipient)
        if author_id is None:
            resp.result_type = create_pb2.CreateResponse.ERROR
            return resp

        # check if local user follows
        follower_flag = self._check_follow(author_id, follower_id)
        if follower_flag == False:
            resp.result_type = create_pb2.CreateResponse.ERROR
            return resp

        # add to article db
        added_flag = self._add_to_posts_db(author_handle, req)
        if added_flag == False:
            resp.result_type = create_pb2.CreateResponse.ERROR
            return resp

        self._logger.debug("Recieve create Article success")
        resp.result_type = create_pb2.CreateResponse.OK
        return resp
