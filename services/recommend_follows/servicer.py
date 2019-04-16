from surprise_recommender import SurpriseRecommender
from noop_recommender import NoopRecommender
from cn_recommender import CNRecommender
from gd_recommender import GraphDistanceRecommender

from services.proto import follows_pb2_grpc
from services.proto import database_pb2
from services.proto import recommend_follows_pb2
from utils.recommenders import RecommendersUtil


class FollowRecommendationsServicer(follows_pb2_grpc.FollowsServicer):

    RECOMMENDERS = {
        'surprise': SurpriseRecommender,
        'cn': CNRecommender,
        'graphdist': GraphDistanceRecommender,
    }
    DEFAULT_RECOMMENDER = 'none'
    ENV_VAR = 'FOLLOW_RECOMMENDER_METHOD'
    DEFAULT_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/8/89/Portrait_Placeholder.png"

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._users_util = users_util
        self._db_stub = db_stub
        self._recommender_util = RecommendersUtil(
            logger, db_stub, self.DEFAULT_RECOMMENDER, self.ENV_VAR, self.RECOMMENDERS)

        # self.active_recommenders contains one or more recommender system
        # objects (out of the constructors in self.RECOMMENDERS).
        self.active_recommenders = self._recommender_util._get_active_recommenders()

    def _get_recommendations(self, user_id):
        '''Get recommendations for users for the given user_id to follow, using
        the one or more systems in self.active_recommenders. Could return empty
        list if there are no good recommendations.'''
        # TODO(iandioch): Allow for combining the results of multiple systems
        # in a smarter way than just concatenation.
        for r in self.active_recommenders:
            yield from r.get_recommendations(user_id)

    def GetFollowRecommendations(self, request, context):
        self._logger.debug('GetFollowRecommendations, user_id = %s',
                           request.user_id)

        resp = recommend_follows_pb2.FollowRecommendationResponse()

        user = self._users_util.get_user_from_db(global_id=request.user_id)
        if user is None:
            resp.result_type = \
                recommend_follows_pb2.FollowRecommendationResponse.ERROR
            resp.error = "Could not find the given user_id."
            return resp

        if not (user.host is None or user.host == ""):
            resp.result_type = \
                recommend_follows_pb2.FollowRecommendationResponse.ERROR
            resp.error = "Can only give recommendations for local users."
            return resp

        resp.result_type = \
            recommend_follows_pb2.FollowRecommendationResponse.OK

        # Get the recommendations and package them into proto.
        for p in self._get_recommendations(user.global_id):
            a = self._users_util.get_or_create_user_from_db(global_id=p[0])
            user_obj = resp.results.add()
            user_obj.handle = a.handle
            user_obj.host = a.host
            user_obj.display_name = a.display_name
            user_obj.bio = a.bio
            user_obj.image = self.DEFAULT_IMAGE
            user_obj.global_id = a.global_id
        return resp

    def UpdateFollowRecommendations(self, request, context):
        resp = recommend_follows_pb2.UpdateFollowRecommendationsResponse()
        for r in self.active_recommenders:
            r.update_recommendations(user_id)
        return resp
