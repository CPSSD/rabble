import os

from collections import defaultdict

from services.proto import database_pb2

class GraphDistanceRecommender:
    '''Recommend based on the "graph distance" similarity metric.
    TODO(iandioch): Explain how this metric works.
    .'''

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._users_util = users_util
        self._db = database_stub

        self._compute_recommendations()

    def _load_data(self):
        users_resp = self._db.AllUsers(database_pb2.AllUsersRequest())
        if users_resp.result_type == database_pb2.UsersResponse.ERROR:
            self._logger.error('Could not get follows from database: %s',
                               users_resp.error)
        return [(u.global_id, u.host_is_null) for u in users_resp.results]

    def _compute_similarity_matrix(self, users):
        '''Compute the similarity matrix for all the users in the users set.
        This is a 2d matrix S where S[u][v] holds the similarity between u
        and v. This is used as the confidence that the system has in
        recommending u should follow v. In this directed graph, S[u][v] may not
        be equal to S[v][u].'''

        def graph_dist(u_id, v_id):
            '''TODO: Explain graph distance metric'''
            # TODO(iandioch): Impl expanding ring.
            return 2

        # Create a 2D matrix to hold the similarity of all user pairs.
        similarity = defaultdict(lambda: defaultdict(int))
        for u_id, u_is_local in users:
            if not u_is_local:
                # Do not calc distances for foreign users.
                continue
            for v_id, v_is_local in users:
                similarity[u_id][v_id] = -graph_dist(u_id, v_id)
        return similarity

    def _get_recommendations(self, users, similarity_matrix):
        recommendations = {}
        for u_id, u_is_local in users:
            if not u_is_local:
                # Do not give recommendations for foreign users.
                continue
            r = []
            for v_id, v_is_local in users:
                if u_id == v_id:
                    # Users already love themselves, no need to recommend they
                    # follow themselves too.
                    continue
                similarity = similarity_matrix[u_id][v_id]
                if similarity == 1:
                    # Already following
                    # TODO(iandioch): Verify this.
                    continue
                r.append((v_id, similarity))

            # Sort by similarity (the most confident recommendation first).
            r.sort(key=lambda x:-x[1])
            if len(r):
                recommendations[u_id] = r
        return recommendations


    def _compute_recommendations(self):
        self._logger.debug(
            'Recomputing recommendations. This may take some time.')
        try:
            # It is necessary to reload data each time, as it may have changed.
            users = self._load_data()
            self._similarity = self._compute_similarity_matrix(users)
            self._recommendations = self._get_recommendations(users,
                                                              self._similarity)
            self._logger.debug('Finished computing recommendations.')
        except Exception as e:
            self._logger.error('Could not compute recommendations:')
            self._logger.error(str(e))


    def get_recommendations(self, user_id):
        if user_id in self._recommendations:
            return self._recommendations[user_id]
        return []
