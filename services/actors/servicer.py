from actor_servicer import ActorServicer
from collection_servicer import CollectionServicer
from services.proto import actor_pb2_grpc


class ActorServicer(actor_pb2_grpc.ActorsServicer):

    def __init__(self, logger, users_util, activities_util, db_stub, host_name):
        self._logger = logger
        self._users_util = users_util
        self._activities_util = activities_util
        self._db_stub = db_stub
        self._host_name = host_name

        actor_servicer = ActorServicer(
            logger, users_util, activities_util, host_name)
        self.Get = actor_servicer.Get

        collection_servicer = CollectionServicer(
            logger, users_util, activities_util, db_stub, host_name)
        self.GetFollowing = collection_servicer.GetFollowing
