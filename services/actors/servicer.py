from actor_servicer import ActorsServicer
from collection_servicer import CollectionServicer
from services.proto import actors_pb2_grpc


class Servicer(actors_pb2_grpc.ActorsServicer):

    def __init__(self, logger, users_util, activities_util, db_stub, host_name, follows_stub):
        self._logger = logger
        self._users_util = users_util
        self._activities_util = activities_util
        self._db_stub = db_stub
        self._host_name = host_name
        self._follows_stub = follows_stub

        actor_servicer = ActorsServicer(
            logger, users_util, activities_util, host_name)
        self.Get = actor_servicer.Get

        collection_servicer = CollectionServicer(
            logger, users_util, activities_util, db_stub, host_name, follows_stub)
        self.GetFollowing = collection_servicer.GetFollowing
        self.GetFollowers = collection_servicer.GetFollowers
