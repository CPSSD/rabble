import urllib3
import json

from proto import create_pb2
from proto import database_pb2


class SendCreateServicer:

    def __init__(self, db_stub, logger):
        self._db_stub = db_stub
        self._logger = logger
        self._client = urllib3.PoolManager()

    def _remove_local_users(self, followers):
        foreign_followers = []
        for follow in followers:
            user_entry = database_pb2.UsersEntry(
                global_id=follow.follower
            )
            user_request = database_pb2.UsersRequest(
                request_type=database_pb2.UsersRequest.FIND,
                match=user_entry
            )
            user_resp = self._db_stub.Users(user_request)
            if (user_resp.result_type == database_pb2.UsersResponse.ERROR or
                len(user_resp.results) < 1):
                self._logger.error(
                    'Could not find follower in db: %s', user_resp.error
                )

            ff = (user_resp.results[0].host, user_resp.results[0].handle)
            foreign_followers.append(ff)
        return foreign_followers

    def _get_follower_list(self, author):
        # get author user_id
        user_entry = database_pb2.UsersEntry(
            handle=author
        )
        user_request = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            match=user_entry
        )
        user_resp = self._db_stub.Users(user_request)
        if (user_resp.result_type == database_pb2.UsersResponse.ERROR or
            len(user_resp.results) < 1):
            self._logger.error('Could not find author in db: %s', user_resp.error)
            return []

        follow_entry = database_pb2.Follow(
            followed=user_resp.results[0].global_id
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry
        )
        follow_resp = self._db_stub.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Could not find any followers: %s', follow_resp.error)
            return []

        return follow_resp.results

    def _post_create_req(self, follower_tuple, req):
        target = follower_tuple[0] + "/" + follower_tuple[1]
        timestamp = req.creation_datetime.ToJsonString()
        create_activity = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Create",
            "to": [target],
            "actor": req.author,
            "object": {
                "type": "Article",
                "name": req.title,
                "published": timestamp,
                "attributedTo": req.author,
                "to": [target],
                "content": req.body
                }
        }
        headers = { "Content-Type": "application/json" }
        target_inbox = follower_tuple[0] + "/ap/" + follower_tuple[1] + "/inbox"
        encoded_body = json.dumps(create_activity).encode('utf-8')
        self._logger.info(target_inbox)

        try:
            r = self._client.request(
                "POST",
                target_inbox,
                body=encoded_body,
                retries=2,
                headers=headers
            )
            self._logger.info(r.status)
            self._logger.info(r)
        except Exception as e:
            self._logger.error("Create activity for follower: %s failed", target)
            self._logger.error(e)


    def SendCreate(self, req, context):
        self._logger.info('Recieved a new create action.')

        # list of follow objects
        follow_list = self._get_follower_list(req.author)
        # remove local users
        foreign_follows = self._remove_local_users(follow_list)

        # go through follow send create activity
        for follower in foreign_follows:
            self._post_create_req(follower, req)

        resp = create_pb2.CreateResponse()
        resp.result_type = create_pb2.CreateResponse.OK
        return resp
