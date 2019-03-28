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
    def _post_create_req(self, follower, req, ap_id, author):
        # Target & actor format is host/@handle e.g. banana.com/@banana
        target = self._activ_util.build_actor(follower.handle, follower.host)
        actor = self._activ_util.build_actor(author.handle, self._host_name)
        timestamp = req.creation_datetime.ToJsonString()
        create_activity = {
            "@context":  self._activ_util.rabble_context(),
            "type": "Create",
            "to": [target],
            "actor": actor,
            "object": {
                "type": "Article",
                "name": req.title,
                "published": timestamp,
                "attributedTo": actor,
                "to": [target],
                "content": req.body,
                "id": ap_id,
            }
        }
        headers = {"Content-Type": "application/ld+json"}

        # s2s inbox for user. Format banana.com/ap/@banana/inbox
        target_inbox = self._activ_util.build_inbox_url(
            follower.handle, follower.host)
        encoded_body = json.dumps(create_activity).encode("utf-8")
        self._logger.info(target_inbox)

        try:
            r = self._client.request(
                "POST",
                target_inbox,
                body=encoded_body,
                retries=2,
                headers=headers
            )
            self._logger.debug(
                "Create activity sent. Response status: %s", r.status)
        except Exception as e:
            self._logger.error(
                "Create activity for follower: %s failed", target)
            self._logger.error(e)

    def SendCreate(self, req, context):
        self._logger.debug("Recieved a new create action.")

        author = self._users_util.get_user_from_db(global_id=req.author_id)
        # Insert ActivityPub ID into database.
        # build author entry from scratch to add host into call
        ap_id = self._activ_util.build_article_url(
            database_pb2.UsersEntry(
                handle=author.handle, host=self._host_name),
            database_pb2.PostsEntry(global_id=req.global_id))
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
            self._post_create_req(follower, req, ap_id, author)

        resp = create_pb2.CreateResponse()
        resp.result_type = create_pb2.CreateResponse.OK
        return resp
