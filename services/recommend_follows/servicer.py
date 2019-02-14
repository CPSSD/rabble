from surprise_recommender import SurpriseRecommender

from services.proto import follows_pb2_grpc
from services.proto import database_pb2
from services.proto import recommend_follows_pb2


class FollowRecommendationsServicer(follows_pb2_grpc.FollowsServicer):

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._users_util = users_util
        self._db_stub = db_stub

        self.recommender = SurpriseRecommender(logger, users_util, db_stub)

    def _get_recommendations(self, user_id):
        # TODO(iandioch): Allow for combining the results of multiple systems.
        self._logger.info("Getting recommendations.")
        print('yo')
        return self.recommender.get_recommendations(user_id)

    def GetFollowRecommendations(self, request, context):
        self._logger.debug('GetFollowRecommendations, username = %s',
                           request.username)

        resp = recommend_follows_pb2.FollowRecommendationResponse()

        handle, host = self._users_util.parse_username(request.username)
        if not (host is None or host == ""):
            resp.result_type = \
                recommend_follows_pb2.FollowRecommendationResponse.ERROR
            resp.error = "Can only give recommendations for local users."
            return resp

        user = self._users_util.get_user_from_db(handle=handle, host=None)
        if user is None:
            resp.result_type = \
                recommend_follows_pb2.FollowRecommendationResponse.ERROR
            resp.error = "Could not find the given username."
            return resp

        resp.result_type = \
            recommend_follows_pb2.FollowRecommendationResponse.OK

        for p in self._get_recommendations(user.global_id):
            a = self._users_util.get_or_create_user_from_db(global_id=p[0])
            user_obj = resp.results.add()
            user_obj.handle = a.handle
            user_obj.host = a.host
            user_obj.display_name = a.display_name
        return resp
