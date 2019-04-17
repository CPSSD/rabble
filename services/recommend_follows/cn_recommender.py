import os

from collections import defaultdict

from services.proto import database_pb2

class CNRecommender:
    '''Recommend based on the "common neighbours" similarity metric. This metric
    uses the number of friends two users have in common to suggest if they
    should connect.

    In our case, this metric suggests U will follow V if U follows many people
    who follow V.
    This works intuitively, however in a decentralised network it could favour
    recommending local users, as it doesn't always know if some other user
    follows V when V is on another instance.'''

    # The minimum number of common neighbours required for another user to be
    # recommended. If this number is higher, the system will only recommend
    # a user if it is quite confident in the link, however users with fewer
    # connections will likely have no recommendations.
    THRESHOLD = 1
    THRESHOLD_ENV_VAR = 'CN_FOLLOW_RECOMMENDER_THRESHOLD'

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._users_util = users_util
        self._db = database_stub

        if (self.THRESHOLD_ENV_VAR in os.environ and
            len(os.environ[self.THRESHOLD_ENV_VAR])):
            try:
                self.THRESHOLD = int(os.environ[self.THRESHOLD_ENV_VAR])
            except e:
                self._logger.warning('Could not load threshold from env var:',
                                     str(e))
        self._logger.debug("CN threshold = {}.".format(self.THRESHOLD))

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
        '''Given the database response with all follows, create the sets of
        out-links and in-links for each user, along with a set of all user IDs
        appearing in the follow graph.'''

        # out_links[x] is the set of nodes with a directed edge from x;
        # ie. the users that x follows.
        out_links = defaultdict(set)
        # in_links[x] is the set of nodes with a directed edge to x;
        # ie. the users that follow x.
        in_links = defaultdict(set)

        # a set of all user ids with associated follows
        users = set()
        for follow in follow_resp.results:
            # We don't want to suggest the user follow someone who doesn't
            # accept follows, so only consider ACTIVE follows.
            if follow.state == follow.ACTIVE:
                out_links[follow.follower].add(follow.followed)
                in_links[follow.followed].add(follow.follower)
                users.add(follow.follower)
                users.add(follow.followed)

        return users, out_links, in_links

    def _compute_similarity_matrix(self, users, out_links, in_links):
        '''Compute the similarity matrix for all the users in the users set.
        This is a 2d matrix S where S[u][v] holds the similarity between u
        and v. This is used as the confidence that the system has in
        recommending u should follow v. In this directed graph, S[u][v] may not
        be equal to S[v][u].'''

        def cn(u, v):
            '''The common neighbours metric suggests if my friends are all
            friends with you, then maybe I would be friends with you too.
            In this directed graph, we interpret this as if many of the people
            I am interested in (ie. the people I follow) are interested in you
            (ie. they follow you) then I will be interested in you (ie. I should
            follow you).
            The CN similarity of me to you is the size of this set of "common
            neighbours". We can compute this by getting the size of the
            intersection of the set of users I follow and the set of users who
            follow you.'''
            return len(out_links[u] & in_links[v])

        # Create a 2D matrix to hold the similarity of all user pairs.
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
                    # v already follows u, no need to give this recommendation.
                    continue
                similarity = similarity_matrix[u][v]
                if similarity < self.THRESHOLD:
                    continue
                r.append((v, similarity))

            # Sort by similarity (the most confident recommendation first).
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

    def update_recommendations(self, user_id):
        return
