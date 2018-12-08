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

    def _generate_article_id(self, author, article_id):
        s = f'{self._host_name}/@{author}/{article_id}'
        if not s.startswith('http'):
            return 'http://' + s
        return s

    def _remove_local_users(self, followers):
        foreign_followers = []
        for follow in followers:
            follower_entry = self._users_util.get_user_from_db(
                global_id=follow.follower
            )
            if follower_entry is None:
                self._logger.error("Could not find follower in db. Id: %s", follow.follower)
                continue
            if follower_entry.host:
                ff = (follower_entry.host, follower_entry.handle)
                foreign_followers.append(ff)
        return foreign_followers

    def _get_follower_list(self, author):
        # get author user_id
        author_entry = self._users_util.get_user_from_db(handle=author)
        if author_entry is None:
            self._logger.error("Could not find author in db")
            return []

        follow_entry = database_pb2.Follow(
            followed=author_entry.global_id
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry
        )
        follow_resp = self._db_stub.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error(
                "Find for followers of id: %s returned error: %s",
                author_entry.global_id,
                follow_resp.error
            )
            return []

        return follow_resp.results

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

    # follower_tuple is (host, handle)
    def _post_create_req(self, follower_tuple, req):
        # Target & actor format is host/@handle e.g. banana.com/@banana
        target = follower_tuple[0] + "/@" + follower_tuple[1]
        actor = self._activ_util.build_actor(req.author, self._host_name)
        timestamp = req.creation_datetime.ToJsonString()
        create_activity = {
            "@context": "https://www.w3.org/ns/activitystreams",
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
                "id": self._generate_article_id(req.author, req.global_id),
            }
        }
        headers = { "Content-Type": "application/ld+json" }

        # s2s inbox for user. Format banana.com/ap/@banana/inbox
        target_inbox = follower_tuple[0] + "/ap/@" + follower_tuple[1] + "/inbox"
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
            self._logger.debug("Create activity sent. Response status: %s", r.status)
        except Exception as e:
            self._logger.error("Create activity for follower: %s failed", target)
            self._logger.error(e)


    def SendCreate(self, req, context):
        self._logger.debug("Recieved a new create action.")

        # Insert ActivityPub ID into database.
        ap_id = self._generate_article_id(req.author, req.global_id)
        err = self._add_ap_id(req.global_id, ap_id)
        if err is not None:
            self._logger.error("Continuing through error: %s", err)

        # list of follow objects
        follow_list = self._get_follower_list(req.author)
        # remove local users
        foreign_follows = self._remove_local_users(follow_list)

        # go through follow send create activity
        # TODO (sailslick) make async/ parallel in the future
        for follower in foreign_follows:
            self._post_create_req(follower, req)

        resp = create_pb2.CreateResponse()
        resp.result_type = create_pb2.CreateResponse.OK
        return resp
