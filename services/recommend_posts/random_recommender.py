from services.proto import database_pb2


class RandomRecommender:
    '''
    Recommend Posts based on a randomly picking posts that the user hasn't liked already
    '''

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._db = database_stub

    def get_recommendations(self, user_id, n):
        return [], None
