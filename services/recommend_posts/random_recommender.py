from services.proto import database_pb2


class RandomRecommender:
    '''
    Recommend Posts based on a randomly picking posts that the user hasn't liked already
    '''

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._db = database_stub

    def get_recommendations(self, user_id, n):
        find_req = database_pb2.RandomPostsRequest(
            num_posts=n,
            user_id=user_id
        )
        find_resp = self._db.RandomPosts(find_req)
        if find_resp.result_type == database_pb2.PostsResponse.ERROR:
            self._logger.info(
                'Got error getting RandomPosts: {}'.format(find_resp.error))
            return [], find_resp.error
        return find_resp.results, None
