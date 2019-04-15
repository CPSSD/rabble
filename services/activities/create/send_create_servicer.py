import urllib3
import json
import os

from services.proto import create_pb2
from services.proto import database_pb2


class SendCreateServicer:

    def __init__(self, db_stub, logger, users_util, activ_util):
        host_name = os.environ.get("HOST_NAME")
        if not host_name:
            print("Please set HOST_NAME env variable")
            sys.exit(1)
        self._host_name = host_name
        self._db_stub = db_stub
        self._logger = logger
        self._users_util = users_util
        self._activ_util = activ_util
        self._client = urllib3.PoolManager()

    def _add_ap_id(self, global_id, ap_id):
        req = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.UPDATE,
            match=database_pb2.PostsEntry(
                global_id=global_id,
            ),
            entry=database_pb2.PostsEntry(
                ap_id=ap_id,
            ),
        )
        resp = self._db_stub.Posts(req)
        if resp.result_type != database_pb2.PostsResponse.OK:
            return "Error inserting ap_id into DB: " + str(resp.error)
        return None

    # follower is (host, handle)
    def _post_create_req(self, follower, req, ap_id, author, article_url):
        target = self._activ_util.build_actor(follower.handle, follower.host)
        actor = self._activ_util.build_actor(author.handle, self._host_name)
        timestamp = req.creation_datetime.ToJsonString()
        article = self._activ_util.build_article(
            ap_id, req.title, timestamp, actor, req.body,
            req.summary, article_url=article_url)
        create_activity = {
            "@context":  self._activ_util.rabble_context(),
            "type": "Create",
            "to": [target],
            "actor": actor,
            "object": article,
        }

        target_inbox = self._activ_util.build_inbox_url(
            follower.handle, follower.host)

        if target_inbox is None:
            self._logger.info("Target inbox is none, skipping.")
            return

        self._logger.info("Sending create activity to foreign server")
        resp, err = self._activ_util.send_activity(
            create_activity, target_inbox, sender_id=author.global_id)
        if err is not None:
            self._logger.error(
                "Send Create to %s error: %s", target_inbox, err)

    def SendCreate(self, req, context):
        self._logger.debug("Recieved a new create action.")

        author = self._users_util.get_user_from_db(global_id=req.author_id)
        # Insert ActivityPub ID into database.
        # build author entry from scratch to add host into call
        ue = database_pb2.UsersEntry(
            handle=author.handle, host=self._host_name)
        pe = database_pb2.PostsEntry(global_id=req.global_id)
        ap_id = self._activ_util.build_article_ap_id(ue, pe)
        article_url = self._activ_util.build_local_article_url(ue, pe)
        err = self._add_ap_id(req.global_id, ap_id)
        if err is not None:
            self._logger.error("Continuing through error: %s", err)

        # list of follow objects
        follow_list = self._users_util.get_follower_list(author.global_id)
        # remove local users
        foreign_follows = self._users_util.remove_local_users(follow_list)

        # go through follow send create activity
        # TODO (sailslick) make async/ parallel in the future
        for follower in foreign_follows:
            self._post_create_req(follower, req, ap_id, author, article_url)

        resp = create_pb2.CreateResponse()
        resp.result_type = create_pb2.CreateResponse.OK
        return resp
