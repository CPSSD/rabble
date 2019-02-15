from collections import defaultdict

from services.proto import database_pb2

class CNRecommender:
    '''Recommend based on the "common neighbours" similarity metric.'''

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._users_util = users_util
        self._db = database_stub
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
        # out_links[x] is the set of nodes with a directed edge from x;
        # ie. the users that x follows.
        out_links = defaultdict(set)
        # in_links[x] is the set of nodes with a directed edge to x;
        # ie. the users that follow x.
        in_links = defaultdict(set)

        # a set of all user ids with associated follows
        users = set()
        for follow in follow_resp.results:
            if follow.state == follow.ACTIVE:
                out_links[follow.follower].add(follow.followed)
                in_links[follow.followed].add(follow.follower)
                users.add(follow.follower)
                users.add(follow.followed)

        return users, out_links, in_links

    def _compute_similarity_matrix(self, users, out_links, in_links):
        # todo: comment explaining what similarity matrix is.
        def cn(u, v):
            # todo: comment
            return len(out_links[u] & in_links[v])

        similarity = defaultdict(lambda: defaultdict(int))
        for u in users:
            for v in users:
                similarity[u][v] = cn(u, v)
        return similarity

    def _get_recommendations(self, users, similarity_matrix, out_links):
        recommendations = {}
        for u in users:
            r = []
            for v in users:
                if u == v:
                    # Users already love themselves, no need to recommend they
                    # follow themselves too.
                    continue
                if v in out_links[u]:
                    # v already follows u, no need to giverecommendation.
                    continue
                r.append((v, similarity_matrix[u][v]))
            # Sort by confidence, descending.
            r.sort(key=lambda x:-x[1])
            if len(r):
                recommendations[u] = r
        return recommendations


    def _compute_recommendations(self):
        self._logger.debug(
            'Recomputing recommendations. This may take some time.')
        try:
            # It is necessary to reload data each time, as it may have changed.
            users, out_links, in_links = self._convert_data(self._load_data())
            self._similarity = self._compute_similarity_matrix(users,
                                                               out_links,
                                                               in_links)
            self._recommendations = self._get_recommendations(users,
                                                              self._similarity,
                                                              out_links)
            self._logger.debug('Finished computing recommendations.')
        except Exception as e:
            self._logger.error('Could not compute recommendations:')
            self._logger.error(str(e))


    def get_recommendations(self, user_id):
        if user_id in self._recommendations:
            return self._recommendations[user_id]
        return []
