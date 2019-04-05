from collections import defaultdict

from services.proto import database_pb2
from utils.recommenders import RecommendersUtil


class CosineRecommender:
    '''
    Calculate similarity based on TF-IDF Cosine-based Similarity method
    described in Content-based Recommendation in Social Tagging Systems (4.3)
    '''

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._db = db_stub
        self._recommender_util = RecommendersUtil(logger, db_stub)
        self.tag_freq = defaultdict()
        self.posts = self._get_all_posts_and_tags()

    def _clean_post_entries(self, pes):
        posts = [{}] * len(pes)
        for i, pe in enumerate(pes):
            tags = self._recommender_util(pe.tags)
            for t in tags:
                self.tag_freq[t] += 1
            posts[i] = {
                "global_id": pe.global_id,
                "tags": tags
            }
        return posts

    def _get_all_posts_and_tags(self):
        find_resp = self._db.TagPosts(database_pb2.PostsRequest())
        if find_resp.result_type == database_pb2.PostsResponse.ERROR:
            self._logger.info(
                'Error getting TagPosts for Cosine: {}'.format(find_resp.error))
            return [], find_resp.error
        return self._clean_post_entries(find_resp.results)

    def get_recommendations(self, user_id, n):
        return [], None
