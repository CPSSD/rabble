from services.proto import actors_pb2
from services.proto import database_pb2


class ActorsServicer:

    def __init__(self, db_stub, logger, users_util, activities_util, host_name):
        self._db_stub = db_stub
        self._logger = logger
        self._users_util = users_util
        self._activities_util = activities_util
        self._host_name = host_name

    def _generate_key_id(self, _id):
        return '{}#main-key'.format(_id)

    def _fetch_public_key_from_database(self, handle):
        user = database_pb2.UsersEntry(
            handle=handle,
            host_is_null=True,
        )
        req = database_pb2.UsersRequest(
            match=user,
            request_type=database_pb2.UsersRequest.FIND
        )
        resp = self._db_stub.Users(req)
        if (resp.result_type != database_pb2.UsersResponse.OK or 
            len(resp.results) == 0):
            self._logger.error('No user found in database')
            return None
        return resp.results[0].public_key

    def _get_public_key(self, handle):
        _id = self._activities_util.build_actor(handle, self._host_name)
        public_key = self._fetch_public_key_from_database(handle)
        return actors_pb2.PublicKey(
            id=self._generate_key_id(_id),
            owner=_id,
            public_key_pem=public_key,
        )

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

        public_key = self._get_public_key(username)
        return actors_pb2.ActorObject(
            type='Person',
            id=actor_url,
            preferredUsername=handle,
            name=user.display_name,
            inbox=inbox_url,
            # TODO(iandioch): Create outbox URL when we have outboxes.
            outbox=None,
            following=following_url,
            followers=followers_url,
            global_id=user.global_id,
            public_key=public_key
        )

    def Get(self, request, context):
        self._logger.debug('Actor requested for {}'.format(request.username))
        actor = self._create_actor(request.username)
        return actors_pb2.ActorResponse(actor=actor)
