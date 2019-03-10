import os

from collections import defaultdict

from services.proto import database_pb2


class GraphDistanceRecommender:
    '''Recommend based on the "graph distance" similarity metric. This metric
    recommends users to follow if they are a short distance away on the
    (directed) follow graph. Realistically, this means it will recommend a user
    follow another user if someone they already follow follows that user.'''

    MAX_DIST = 4
    MAX_DIST_ENV_VAR = 'GRAPH_DIST_FOLLOW_RECOMMENDER_MAX_DIST'

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._users_util = users_util
        self._db = database_stub

        if (self.MAX_DIST_ENV_VAR in os.environ and
                len(os.environ[self.MAX_DIST_ENV_VAR])):
            try:
                self.MAX_DIST = int(os.environ[self.MAX_DIST_ENV_VAR])
            except e:
                self._logger.warning('Could not load max dist from env var:',
                                     str(e))
        self._logger.debug("Graph max dist = {}.".format(self.MAX_DIST))

        self._compute_recommendations()

    def _load_data(self):
        users_resp = self._db.AllUsers(database_pb2.AllUsersRequest())
        if users_resp.result_type == database_pb2.UsersResponse.ERROR:
            self._logger.error('Could not get users from database: %s',
                               users_resp.error)
        return [(u.global_id, u.host_is_null) for u in users_resp.results]

    def _get_neighbours(self, uid, inverse=False):
        '''Get the neighbours of the user with the given uid.

        If `inverse` is False, then this returns the IDs of users who the given
        user follows.
        If `inverse` is True, then this returns the IDs of users who follow the
        given user.'''
        follow = database_pb2.Follow(follower=uid)
        if inverse:
            follow = database_pb2.Follow(followed=uid)
        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            entry=follow
        )
        resp = self._db.Follow(req)
        if resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error('Could not get follows from database: %s',
                               resp.error)
        return [(f.follower if inverse else f.followed) for f in resp.results]

    def _compute_similarity_matrix(self, users):
        '''Compute the similarity matrix for all the users in the users set.
        This is a 2d matrix S where S[u][v] holds the similarity between u
        and v. This is used as the confidence that the system has in
        recommending u should follow v. In this directed graph, S[u][v] may not
        be equal to S[v][u].'''

        def expand(s, inverse=False):
            '''Expand the given set `s`. If `inverse` is set to true, it will
            expand this set using inverse follows instead of direct follows.'''
            for u_id in set(s):
                s.update(self._get_neighbours(u_id, inverse=inverse))

        def graph_dist(u_id, v_id):
            '''The graph distance metric suggests if you are close on the
            follow graph, then I should follow you. This means if I follow 
            someone who follows you, the distance from me to you is 2, and I
            am likely to be interested in following you. If I follow someone
            who follows someone else who follows you, the distance is 3; etc.
            This metric is likely to compute many users to be at the same
            distance.

            Here, we evaluate the graph distance between two users by using the
            method given in 'Scalable Proximity Estimation and Link Prediction
            in Online Social Networks' by Han Hee Song, Tae Won Cho, Vacha
            Dave, Yin Zhang, Lili Qiu, which avoids keeping the whole follow
            graph in memory at once, and instead uses an expanding ring search
            to compute the distance'''

            # The source set; initialised to just contain the active  user.
            s = set([u_id])
            # The destination set; initialised to just contain the target user.
            d = set([v_id])
            dist = 0

            # Keep iterating while the set intersection of S and D is empty;
            # ie. as soon as we find some element in the intersection set, we
            # can stop iterating, as we have found a route from S to D.
            while len(s & d) == 0:
                if dist > self.MAX_DIST:
                    # We have gone deep enough; give up.
                    break
                dist += 1

                # We must either expand S to include all users who users of S
                # follow, or expand D to include all users who follow
                # someone in D (ie. inverse follows).
                # For efficiency, we always choose the smaller set between S
                # and D to expand.
                if len(d) < len(s):
                    old_size = len(d)
                    # Expand D by adding in the inverse follows.
                    expand(d, inverse=True)
                    new_size = len(d)
                    if old_size == new_size:
                        # Set didn't change, so we can exit early.
                        break
                else:
                    old_size = len(s)
                    # Expand S by adding the directly followed users.
                    expand(s)
                    new_size = len(s)
                    if old_size == new_size:
                        # Set didn't change, so we can exit early.
                        break

            return dist

        # Create a 2D matrix to hold the similarity of all user pairs.
        similarity = defaultdict(lambda: defaultdict(int))
        for u_id, u_is_local in users:
            if not u_is_local:
                # Do not calc distances for foreign users.
                continue
            for v_id, v_is_local in users:
                # Negate the graph distance, as we want a low-numbered graph
                # distance to mean a high-numbered similarity level.
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
            r.sort(key=lambda x: -x[1])
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
