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
        self.algo = self._fit_model()

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
            # TODO(iandioch): Consider follow state.
            user_id.append(follow.follower)
            item_id.append(follow.followed)
            rating.append(1)

        d = {'follower': user_id, 'followee': item_id, 'rating': rating}
        df = pd.DataFrame(data=d)

        reader = Reader(rating_scale=(0, 1))
        return Dataset.load_from_df(df[['follower', 'followee', 'rating']],
                                    reader)


    def _fit_model(self):
        data = self._convert_data(self._load_data())
        algo = SVD()
        cross_validate(algo, data, measures=['RMSE', 'MAE'], cv=5, verbose=True)
        return algo

    def GetFollowRecommendations(self, request, context):
        self._logger.debug('GetFollowing, username = %s', request.username)


        return None
