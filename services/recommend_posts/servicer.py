import os

from random_recommender import RandomRecommender
from cosine_recommender import CosineRecommender

from services.proto import database_pb2
from services.proto import recommend_posts_pb2_grpc
from services.proto import recommend_posts_pb2
from utils.recommenders import RecommendersUtil
from utils.activities import ActivitiesUtil


class PostRecommendationsServicer(recommend_posts_pb2_grpc.PostRecommendationsServicer):

    RECOMMENDERS = {
        'random': RandomRecommender,
        'cosine': CosineRecommender,
    }
    DEFAULT_RECOMMENDER = 'random'
    ENV_VAR = 'POSTS_RECOMMENDER_METHOD'
    MAX_RECOMMENDATIONS = 50
    DEFAULT_IMAGE = "http://clipart-library.com/images/8iGbjxgjT.jpg"

    def __init__(self, users_util, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub
        self._users_util = users_util
        self._activ_util = ActivitiesUtil(logger, db_stub)
        self._recommender_util = RecommendersUtil(
            logger, db_stub, self.DEFAULT_RECOMMENDER, self.ENV_VAR, self.RECOMMENDERS)

        # self.active_recommenders contains one or more recommender system
        # objects (out of the constructors in self.RECOMMENDERS).
        self.active_recommenders = self._recommender_util._get_active_recommenders()

    def Get(self, request, context):
        self._logger.debug('Get PostRecommendations, user_id = %s',
                           request.user_id)

        resp = recommend_posts_pb2.PostRecommendationsResponse()

        recommended_posts = []
        post_ids = set()
        max_posts_per_r = self.MAX_RECOMMENDATIONS // len(
            self.active_recommenders)
        for r in self.active_recommenders:
            r_posts, error = r.get_recommendations(
                request.user_id, max_posts_per_r)
            if error:
                resp.result_type = \
                    recommend_posts_pb2.PostRecommendationsResponse.ERROR
                resp.message = error
                return resp
            recommended_posts.append(r_posts)

        # Join recommendations together, with the highest recommended first
        posts = []
        for i in range(max_posts_per_r + 1):
            for r_p in recommended_posts:
                # See proto/Feed.Post and proto/database.PostsEntry
                if i < len(r_p):
                    author = self._users_util.get_user_from_db(
                        global_id=r_p[i].author_id)
                    if author == None:
                        resp.result_type = \
                            recommend_posts_pb2.PostRecommendationsResponse.ERROR
                        resp.message = "Post Author could not be found"
                        return resp
                    post_obj = resp.results.add()
                    post_obj.global_id = r_p[i].global_id
                    post_obj.author = author.handle
                    post_obj.author_host = author.host
                    post_obj.author_id = r_p[i].author_id
                    post_obj.title = r_p[i].title
                    post_obj.body = r_p[i].body
                    post_obj.published = self._activ_util.timestamp_to_rfc(
                        r_p[i].creation_datetime)
                    post_obj.likes_count = r_p[i].likes_count
                    post_obj.bio = author.bio
                    post_obj.image = self.DEFAULT_IMAGE
                    post_obj.is_liked = r_p[i].is_liked
                    post_obj.is_followed = r_p[i].is_followed
                    post_obj.shares_count = r_p[i].shares_count
                    post_obj.summary = r_p[i].summary
                    tags = self._recommender_util.split_tags(r_p[i].tags)
                    post_obj.tags.extend(tags)
        resp.result_type = \
            recommend_posts_pb2.PostRecommendationsResponse.OK
        return resp

    def UpdateModel(self, request, context):
        self._logger.debug('UpdateModel PostRecommendations, user_id = %s',
                           request.user_id)

        resp = recommend_posts_pb2.PostRecommendationsResponse()

        for r in self.active_recommenders:
            error = r.update_model(request.user_id, request.article_id)
            if error:
                resp.result_type = \
                    recommend_posts_pb2.PostRecommendationsResponse.ERROR
                resp.message = error
                return resp

        resp.result_type = \
            recommend_posts_pb2.PostRecommendationsResponse.OK
        return resp

    def AddPost(self, request, context):
        self._logger.debug('UpdateModel PostRecommendations, user_id = %s',
                           request.author_id)

        resp = recommend_posts_pb2.PostRecommendationsResponse()

        for r in self.active_recommenders:
            error = r.add_post(request)
            if error:
                resp.result_type = \
                    recommend_posts_pb2.PostRecommendationsResponse.ERROR
                resp.message = error
                return resp

        resp.result_type = \
            recommend_posts_pb2.PostRecommendationsResponse.OK
        return resp
