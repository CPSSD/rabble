from services.proto import actors_pb2
from services.proto import follows_pb2
import json


class CollectionServicer:

    def __init__(self, logger, users_util, activities_util, db_stub, host_name, follows_stub):
        self._logger = logger
        self._users_util = users_util
        self._activities_util = activities_util
        self._db_stub = db_stub
        self._host_name = host_name
        self._follows_stub = follows_stub

    def _convert_follow_user_to_person(self, follow_user):
        # convert follows.proto/FollowUser to an activitypub Person object

        # TODO(sailslick) add actor_url to user db. Foreign users will have different endpoints
        host = follow_user.host
        if follow_user.host is None or follow_user.host == "":
            host = self._host_name
        follower_uri = self._activities_util.build_actor(
            follow_user.handle, host)
        return {
            "type": "Person",
            "name": follow_user.handle,
            "url": follower_uri
        }

    def _create_following(self, username):
        user = self._users_util.get_user_from_db(handle=username, host=None)
        if user is None:
            self._logger.warning('Could not find user in database.')
            return None

        summary = "Collection of users " + user.handle + " is following"
        followsRequest = follows_pb2.GetFollowsRequest(username=user.handle)
        gfr = self._follows_stub.GetFollowing(followsRequest)

        if gfr.result_type == follows_pb2.GetFollowsResponse.ERROR:
            self._logger.error(
                "GetFollowing for following collection returned error: %s",
                gfr.error
            )
            return None

        user_list = [self._convert_follow_user_to_person(x) for x in gfr.results]

        collection = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "summary": summary,
            "type": "Collection",
            "totalItems": len(gfr.results),
            "items": user_list
        }

        return json.dumps(collection)

    def GetFollowing(self, request, context):
        self._logger.debug('Following collection requested for {}'.format(request.username))
        collection = self._create_following(request.username)
        return actors_pb2.CollectionResponse(collection=collection)
