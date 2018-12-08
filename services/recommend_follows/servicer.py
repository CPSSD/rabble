from get_servicer import GetFollowRecommendationsServicer

from services.proto import follows_pb2_grpc


class FollowRecommendationsServicer(follows_pb2_grpc.FollowsServicer):

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._users_util = users_util
        self._db_stub = db_stub

        recommendations_servicer = GetFollowRecommendationsServicer(logger,
                                                                    users_util,
                                                                    db_stub)
        self.GetFollowRecommendations = \
            recommendations_servicer.GetFollowRecommendations
