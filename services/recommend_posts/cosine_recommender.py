from math import log
from collections import defaultdict
from heapq import heappush, heappushpop

from services.proto import database_pb2
from utils.recommenders import RecommendersUtil
from utils.articles import get_article


class CosineRecommender:
    '''
    Calculate similarity based on TF-IDF cosine-based similarity method
    described in Content-based Recommendation in Social Tagging Systems (4.3)
    '''

    def __init__(self, logger, users_util, db_stub):
        self._logger = logger
        self._db = db_stub
        self._recommender_util = RecommendersUtil(logger, db_stub)

        # Get user data and create models
        self.post_tag_freq = defaultdict(int)
        self.user_tag_freq = defaultdict(int)
        self.posts = self._get_all_posts_and_tags()
        self._logger.info("post-tags: {}".format(self.posts))
        self.users = self._get_all_user()
        self.user_models = self._create_user_models(self.users)
        self._logger.info("user_models: {}".format(self.user_models))

        # Calculate Inverse Frequencies
        self.user_tag_ifs = self._calculate_based_itf(
            self.user_tag_freq, len(self.user_models))
        self.post_tag_ifs = self._calculate_based_itf(
            self.post_tag_freq, len(self.posts))

    def _calculate_based_itf(self, tag_freq, N):
        itfs = defaultdict(int)
        for key in tag_freq.keys():
            itf = log(N / tag_freq[key])
            itfs[key] = itf
        return itfs

    def _clean_post_entries(self, pes):
        # Create an array with length the same as highest post id to allow
        # indexing by global_id
        highest_post_id = max(pes, key=lambda x: x.global_id).global_id + 1
        posts = [{"global_id": 0, "tags": []}] * highest_post_id
        for pe in pes:
            tags = self._recommender_util.split_tags(pe.tags)
            for t in tags:
                self.post_tag_freq[t] += 1
            posts[pe.global_id] = {
                "global_id": pe.global_id,
                "tags": tags
            }
        return posts

    def _clean_user_entries(self, ues):
        # Create an array of with length same as highest user id to allow
        # indexing by global_id
        highest_user_id = max(ues, key=lambda x: x.global_id).global_id + 1
        users = [{"global_id": 0, "likes": []}] * highest_user_id
        for ue in ues:
            likes = self._clean_likes(ue.likes)
            if not ue.host_is_null:
                # Do not generate anything for foreign users.
                continue
            users[ue.global_id] = {
                "global_id": ue.global_id,
                "likes": likes
            }
        return users

    def _clean_likes(self, likes):
        # The GROUP_CONCAT method in sqlite joins objects with "," into a string
        return [int(x) for x in likes.split(",") if x != ""]

    def _create_user_models(self, users):
        # Iterate over every user like and add all tags of that post to the user
        # model
        user_models = defaultdict(lambda: defaultdict(int))
        for u in users:
            for post_id in u["likes"]:
                for tag in self.posts[post_id]["tags"]:
                    self.user_tag_freq[tag] += 1
                    user_models[u["global_id"]][tag] += 1
        return user_models

    def _get_all_posts_and_tags(self):
        find_resp = self._db.TaggedPosts(database_pb2.PostsRequest())
        if find_resp.result_type == database_pb2.PostsResponse.ERROR:
            self._logger.error(
                'Error getting TaggedPosts for Cosine: {}'.format(find_resp.error))
            return []
        return self._clean_post_entries(find_resp.results)

    def _get_all_user(self):
        find_resp = self._db.AllUserLikes(database_pb2.AllUsersRequest())
        if find_resp.result_type == database_pb2.UsersResponse.ERROR:
            self._logger.error(
                'Error getting AllUserLikes for Cosine: {}'.format(find_resp.error))
            return []

        return self._clean_user_entries(find_resp.results)

    def _tf_idf_cosine_similarity(self, user_model, post_tags):
        sum_user_item_tf = 0
        sum_user_tf = 0
        sum_item_tf = 0
        for tag in post_tags:
            sum_user_item_tf += user_model[tag] * \
                self.user_tag_ifs[tag] * self.post_tag_ifs[tag]
            sum_user_tf += (user_model[tag] * self.user_tag_ifs[tag]) ** 2
            sum_item_tf += self.post_tag_ifs[tag] ** 2
        divisor = (((sum_user_tf) ** 0.5) * ((sum_item_tf) ** 0.5))
        if divisor == 0:
            return -1
        tf_cosine = sum_user_item_tf / divisor
        return tf_cosine

    def get_recommendations(self, user_id, n):
        u_m = self.user_models[user_id]
        if u_m == {}:
            self._logger.info(
                'Cosine user_model is empty. id: {}'.format(user_id))
            return [], None

        # Calculate similarities
        sims = []
        for p in self.posts:
            # do not recommend liked posts
            if p["global_id"] in self.users[user_id]["likes"]:
                continue
            sim = self._tf_idf_cosine_similarity(u_m, p["tags"])
            if len(sims) < n:
                heappush(sims, (sim, p["global_id"]))
            else:
                heappushpop(sims, (sim, p["global_id"]))

        # get top n results
        sims = sorted(sims, reverse=True)
        self._logger.info('Recommended (score, id): {}'.format(sims))
        posts_entries = []
        for result in sims:
            art = get_article(self._logger, self._db, global_id=result[1])
            posts_entries.append(art)
        return posts_entries
