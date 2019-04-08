from collections import defaultdict

from services.proto import database_pb2
from utils.recommenders import RecommendersUtil


class CosineRecommender:
    '''
    Calculate similarity based on TF-IDF cosine-based similarity method
    described in Content-based Recommendation in Social Tagging Systems (4.3)
    '''

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._db = db_stub
        self._recommender_util = RecommendersUtil(logger, db_stub)
        self.tag_freq = defaultdict(int)
        self.posts = self._get_all_posts_and_tags()
        self._logger.info("post-tags: {}".format(self.posts))
        self.user_models = self._get_all_user_models()
        self._logger.info("user_models: {}".format(self.user_models))

    def _clean_post_entries(self, pes):
        # Create an array of with length same as highest post id to allow
        # indexing by global_id
        highest_post_id = max(pes, key=lambda x: x.global_id).global_id + 1
        posts = [{}] * highest_post_id
        for pe in pes:
            tags = self._recommender_util.split_tags(pe.tags)
            for t in tags:
                self.tag_freq[t] += 1
            posts[pe.global_id] = {
                "global_id": pe.global_id,
                "tags": tags
            }
        return posts

    def _clean_likes(self, likes):
        # The GROUP_CONCAT method in sqlite joins objects with "," into a string
        return [int(x) for x in likes.split(",") if x != ""]

    def _create_user_models(self, users):
        # Iterate over every user like and add all tags of that post to the user
        # model
        user_models = defaultdict(lambda: defaultdict(int))
        for u in users:
            for post_id in self._clean_likes(u.likes):
                for tag in self.posts[post_id]["tags"]:
                    user_models[u.global_id][tag] += 1
        return user_models

    def _get_all_posts_and_tags(self):
        find_resp = self._db.TagPosts(database_pb2.PostsRequest())
        if find_resp.result_type == database_pb2.PostsResponse.ERROR:
            self._logger.error(
                'Error getting TagPosts for Cosine: {}'.format(find_resp.error))
            return []
        return self._clean_post_entries(find_resp.results)

    def _get_all_user_models(self):
        find_resp = self._db.AllUserLikes(database_pb2.AllUsersRequest())
        if find_resp.result_type == database_pb2.UsersResponse.ERROR:
            self._logger.error(
                'Error getting AllUserLikes for Cosine: {}'.format(find_resp.error))
            return []

        return self._create_user_models(find_resp.results)

    def get_recommendations(self, user_id, n):
        return [], None
