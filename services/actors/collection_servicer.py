from services.proto import actors_pb2


class CollectionServicer:

    def __init__(self, logger, users_util, activities_util, db_stub, host_name):
        self._logger = logger
        self._users_util = users_util
        self._activities_util = activities_util
        self._db_stub = db_stub
        self._host_name = host_name

    def _create_following(self, username):
        user = self._users_util.get_user_from_db(handle=username, host=None)
        if user is None:
            self._logger.warning('Could not find user in database.')
            return None

        handle = user.handle
        inbox_url = self._activities_util.build_inbox_url(handle,
                                                          self._host_name)
        following_url = inbox_url + "/following.json"
        return actors_pb2.ActorObject(
            type='Person',
            preferredUsername=handle,
            name=user.display_name,
            inbox=inbox_url,
            # TODO(iandioch): Create outbox URL when we have outboxes.
            outbox=None,
            following=following_url,
        )

    def GetFollowing(self, request, context):
        self._logger.debug('Following collection requested for {}'.format(request.username))
        collection = self._create_following(request.username)
        return actors_pb2.CollectionResponse(collection=collection)
