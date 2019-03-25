import os

from random_recommender import RandomRecommender

from services.proto import posts_pb2_grpc
from services.proto import database_pb2
from services.proto import recommend_posts_pb2
from utils.recommenders import RecommendersUtil


class PostRecommendationsServicer(posts_pb2_grpc.PostsServicer):

    RECOMMENDERS = {
        'random': RandomRecommender,
    }
    DEFAULT_RECOMMENDER = 'random'
    ENV_VAR = 'POSTS_RECOMMENDER_METHOD'
    MAX_RECOMMENDATIONS = 50

    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub
        self._recommender_util = RecommendersUtil(
            logger, db, DEFAULT_RECOMMENDER, ENV_VAR, RECOMMENDERS)

        # self.active_recommenders contains one or more recommender system
        # objects (out of the constructors in self.RECOMMENDERS).
        self.active_recommenders = self._recommender_util._get_active_recommenders()

    def Get(self, request, context):
        self._logger.debug('Get PostRecommendations, user_id = %s',
                           request.user_id)

        resp = recommend_posts_pb2.PostRecommendationsResponse()

        recommended_posts = []
        post_ids = set()
        max_posts_per_r = MAX_RECOMMENDATIONS // len(self.active_recommenders)
        for r in self.active_recommenders:
            r_posts, error = r.get_recommendations(user_id, max_posts_per_r)
            if error:
                resp.result_type = \
                    recommend_posts_pb2.PostRecommendationsResponse.ERROR
                resp.message = error
                return resp
            recommended_posts.append(r_posts)

        # Join recommendations together, with the highest recommended first
        posts = []
        for i in range(max_posts_per_r + 1):
            for r_p in recommend_posts:
                if i < len(r_p):
                    posts.append(r_p[i])
        resp.result_type = \
            recommend_posts_pb2.PostRecommendationsResponse.OK
        resp.results = posts
        return resp
