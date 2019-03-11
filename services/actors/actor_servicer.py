from services.proto import actors_pb2


class ActorsServicer:

    def __init__(self, logger, users_util, activities_util, host_name):
        self._logger = logger
        self._users_util = users_util
        self._activities_util = activities_util
        self._host_name = host_name

    def _create_actor(self, username):
        user = self._users_util.get_user_from_db(handle=username,
                                                 host_is_null=True)
        if user is None:
            self._logger.warning('Could not find user in database.')
            return None

        handle = user.handle
        inbox_url = self._activities_util.build_inbox_url(handle,
                                                          self._host_name)
        actor_url = self._activities_util.build_actor(handle, self._host_name)
        following_url = actor_url + "/following"
        followers_url = actor_url + "/followers"
        return actors_pb2.ActorObject(
            type='Person',
            preferredUsername=handle,
            name=user.display_name,
            inbox=inbox_url,
            # TODO(iandioch): Create outbox URL when we have outboxes.
            outbox=None,
            following=following_url,
            followers=followers_url,
            global_id=user.global_id,
        )

    def Get(self, request, context):
        self._logger.debug('Actor requested for {}'.format(request.username))
        actor = self._create_actor(request.username)
        return actors_pb2.ActorResponse(actor=actor)
