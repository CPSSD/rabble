from services.proto import database_pb2


class CosineRecommender:
    '''
    Calculate similarity based on TF-IDF Cosine-based Similarity method
    described in Content-based Recommendation in Social Tagging Systems (4.3)
    '''

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._db = database_stub

    def get_recommendations(self, user_id, n):
        return [], None
