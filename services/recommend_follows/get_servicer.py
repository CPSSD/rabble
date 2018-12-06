from collections import defaultdict
from enum import Enum

from services.proto import database_pb2
from services.proto import recommend_follows_pb2

import pandas as pd

from surprise import Dataset, Reader, SVD
from surprise.model_selection import cross_validate


class GetFollowRecommendationsServicer:

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._users_util = users_util
        self._db = database_stub
        # A dict of the form {user_id: [(recommended_user_id, confidence)]}.
        self._predictions = {}
        self._compute_recommendations()

    def _load_data(self):
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=None)
        follow_resp = self._db.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Could not get follows from database: %s',
                               follow_resp.error)
        return follow_resp

    def _convert_data(self, follow_resp):
        # Must be (user_id, item_id, rating)
        d = [[], [], []]
        user_id = []
        item_id = []
        rating = []
        for follow in follow_resp.results:
            # Do not have to worry about follow state, because even a rejected
            # follow is still a strong signal of interest by the followee.
            user_id.append(follow.follower)
            item_id.append(follow.followed)
            rating.append(1)

        d = {'follower': user_id, 'followee': item_id, 'rating': rating}
        df = pd.DataFrame(data=d)

        reader = Reader(rating_scale=(0, 1))
        return Dataset.load_from_df(df[['follower', 'followee', 'rating']],
                                    reader)

    def _fit_model(self, data):
        algo = SVD()
        cross_validate(algo, data, measures=[
                       'RMSE', 'MAE'], cv=5, verbose=True)
        return algo

    # Returns a dict of form {user_id: [recommendation]}, where recommendation
    # is a tuple consisting of (user_to_follow_id, confidence_score). Each list
    # of recommendations should be of length n.
    def _top_n(self, algo, data, n=8):
        # Should contain all entries NOT in the trainset.
        testset = data.build_full_trainset().build_anti_testset()
        pred = algo.test(testset)
        user = defaultdict(list)
        for follower, followed, _, est, _ in pred:
            if follower == followed:
                # Never recommend a user follow themselves, no matter how much
                # they'd love themselves.
                continue
            user[follower].append((followed, est))

        for u in user:
            user[u].sort(key=lambda x: x[1], reverse=True)
            user[u] = user[u][:n]
        return user

    def _compute_recommendations(self):
        self._logger.debug(
            'Recomputing recommendations. This may take some time.')
        # It is necessary to reload data each time, as it may have changed.
        self._data = self._convert_data(self._load_data())
        self._algo = self._fit_model(self._data)
        self._predictions = self._top_n(self._algo, self._data)
        self._logger.debug('Finished computing recommendations.')

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

        user_id = user.global_id
        if user_id not in self._predictions:
            resp.result_type = \
                recommend_follows_pb2.FollowRecommendationResponse.ERROR
            resp.error = "No recommendations found for this user."
            return resp

        resp.result_type = \
            recommend_follows_pb2.FollowRecommendationResponse.OK
        for p in self._predictions[user_id]:
            a = self._users_util.get_or_create_user_from_db(global_id=p[0])
            user_obj = resp.results.add()
            user_obj.handle = a.handle
            user_obj.host = a.host
            user_obj.display_name = a.display_name
        return resp
