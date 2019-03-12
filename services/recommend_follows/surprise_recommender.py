import random

from collections import defaultdict
from enum import Enum

from services.proto import database_pb2

import pandas as pd

from surprise import Dataset, Reader, SVD
from surprise.model_selection import cross_validate


class SurpriseRecommender:

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

        follows = defaultdict(set)
        inverse_follows = defaultdict(set)
        for follow in follow_resp.results:
            # Do not have to worry about follow state, because even a rejected
            # follow is still a strong signal of interest by the followee.
            user_id.append(follow.follower)
            item_id.append(follow.followed)
            rating.append(1)

            follows[follow.follower].add(follow.followed)
            inverse_follows[follow.followed].add(follow.follower)

        # Now randomly put zeros in non-existing links in the network.
        # This is necessary as the problem is an example of PU-learning, where
        # we have no negative samples to "drag down" the recommendation
        # confidence. That's to say, without zeros, the model will never have
        # incentive not to recommend everyone, as it is never told that an 
        # unsuitable recommendation is bad.
        self._logger.debug('Assigning zeros randomly.')

        # Create a set of all users we can create recommendations for by
        # getting the set union of both sides of all follow connections.
        all_users = tuple(set(follows) | set(inverse_follows))

        # We only want to add as many zeros as there are ones.
        num_zeros_added = 0
        num_ones = len(follow_resp.results)

        # Important to keep track of attempts to randomly add zeros, so that
        # in a densely connected graph (eg. on a small instance where everyone
        # follows everyone else) the loop doesn't continue forever.
        # We set the max attempts (rather arbitrarily) to the square of the
        # number of different users; this is the number of possible ways of
        # choosing two random users from the set of all users.
        num_attempts = 0
        max_attempts = len(all_users)**2

        # Continue adding zeros until there are the same number as there are
        # ones, or until we give up.
        while num_zeros_added < num_ones and num_attempts < max_attempts:
            num_attempts += 1
            follower = random.choice(all_users)
            followed = random.choice(all_users)

            if follower == followed:
                # Cannot follow yourself.
                continue
            if followed in follows[follower]:
                # Follow already exists.
                continue

            user_id.append(follower)
            item_id.append(followed)
            rating.append(0)
            num_zeros_added += 1

        d = {'follower': user_id, 'followee': item_id, 'rating': rating}
        df = pd.DataFrame(data=d)

        reader = Reader(rating_scale=(0, 1))
        return Dataset.load_from_df(df[['follower', 'followee', 'rating']],
                                    reader)

    def _fit_model(self, data):
        algo = SVD()
        cross_validate(algo,
                       data,
                       measures=['RMSE', 'MAE'],
                       cv=5,
                       verbose=True)
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
        try:
            # It is necessary to reload data each time, as it may have changed.
            self._data = self._convert_data(self._load_data())
            self._algo = self._fit_model(self._data)
            self._predictions = self._top_n(self._algo, self._data)
            self._logger.debug('Finished computing recommendations.')
        except Exception as e:
            self._logger.error('Could not compute recommendations:')
            self._logger.error(str(e))

    def get_recommendations(self, user_id):
        if user_id not in self._predictions:
            return []
        return self._predictions[user_id]
