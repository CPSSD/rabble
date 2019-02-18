from services.proto import actors_pb2, actors_pb2_grpc


class ActorsServicer(actors_pb2_grpc.ActorsServicer):

    def __init__(self, logger, users_util, activities_util, db_stub, host_name):
        self._logger = logger
        self._users_util = users_util
        self._activities_util = activities_util
        self._db_stub = db_stub
        self._host_name = host_name

    def _create_actor(self, username):
        user = self._users_util.get_user_from_db(handle=username, host_is_null=True)
        if user is None:
            self._logger.warning('Could not find user in database.')
            return None

        handle = self._users_util.parse_username(username)[0]
        inbox_url = self._activities_util.build_inbox_url(handle,
                                                          self._host_name)
        return actors_pb2.ActorObject(
            type='Person',
            preferredUsername=handle,
            name=user.display_name,
            inbox=inbox_url,
            # TODO(iandioch): Create outbox URL when we have outboxes.
            outbox=None,
        )

    def Get(self, request, context):
        self._logger.debug('Actor requested for {}'.format(request.username))
        actor = self._create_actor(request.username)
        return actors_pb2.ActorResponse(actor=actor)
