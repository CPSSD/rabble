from services.proto import actors_pb2, actors_pb2_grpc


class ActorsServicer(actors_pb2_grpc.ActorsServicer):

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._users_util = users_util
        self._db_stub = db_stub

    def _create_actor(self, username):
        user = self._users_util.get_user_from_db(handle=username, host=None)
        if user is None:
            self._logger.warning('Could not find user in database.')
            return None
        return actors_pb2.ActorObject(
            type='Person',
            preferredUsername=self._users_util.parse_username(username)[0],
            name=user.display_name,
        )

    def Get(self, request, context):
        self._logger.debug('Actor requested for {}'.format(request.username))
        actor = self._create_actor(request.username)
        return actors_pb2.ActorResponse(actor=actor)
