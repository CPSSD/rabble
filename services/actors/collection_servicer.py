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

        return self._activities_util.build_actor(follow_user.handle, host)

    def _create_collection(self, summary, item_list):
        collection = {
            "@context":  self._activities_util.rabble_context(),
            "summary": summary,
            "type": "Collection",
            "totalItems": len(item_list),
            "items": item_list
        }

        return json.dumps(collection)

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
        return self._create_collection(summary, user_list)

    def _create_followers(self, username):
        user = self._users_util.get_user_from_db(handle=username, host=None)
        if user is None:
            self._logger.warning('Could not find user in database.')
            return None

        summary = "Collection of users following " + user.handle
        followsRequest = follows_pb2.GetFollowsRequest(username=user.handle)
        gfr = self._follows_stub.GetFollowers(followsRequest)

        if gfr.result_type == follows_pb2.GetFollowsResponse.ERROR:
            self._logger.error(
                "GetFollowers for followers collection returned error: %s",
                gfr.error
            )
            return None

        user_list = [self._convert_follow_user_to_person(x) for x in gfr.results]
        return self._create_collection(summary, user_list)

    def GetFollowing(self, request, context):
        self._logger.debug('Following collection requested for {}'.format(request.username))
        collection = self._create_following(request.username)
        return actors_pb2.CollectionResponse(collection=collection)

    def GetFollowers(self, request, context):
        self._logger.debug('Followers collection requested for {}'.format(request.username))
        collection = self._create_followers(request.username)
        return actors_pb2.CollectionResponse(collection=collection)
