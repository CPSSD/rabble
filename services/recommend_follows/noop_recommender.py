class NoopRecommender:
    '''A recommender method that doesn't give any recommendations. You can use
    this class as a base when creating other recommender methods.'''

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._users_util = users_util
        self._db = database_stub

    def get_recommendations(self, user_id):
        return []
