import json
import time
from services.proto import database_pb2
from utils.users import UsersUtil


class RecommendersUtil:
    def __init__(self, logger, db, default, env_var, recommenders):
        self._logger = logger
        self._db_stub = db
        self._users_util = UsersUtil(logger, db)
        self.DEFAULT_RECOMMENDER = default
        self.ENV_VAR = env_var
        self.RECOMMENDERS = recommenders

    def _get_active_recommenders(self):
        '''Get the list of recommender system objects based on an env
        var (self.ENV_VAR) provided by the user. The user can give a
        comma-separated list of system names (from self.RECOMMENDERS), and
        this function will return the recommender objects for these names.

        If the env var is not set, or no valid names are provided, then a
        default system (self.DEFAULT_RECOMMENDER) will be used.'''
        keys = [self.DEFAULT_RECOMMENDER]
        if self.ENV_VAR not in os.environ or os.environ[self.ENV_VAR] == "":
            self._logger.warning('No value set for "follow_recommender" ' +
                                 'environment variable, using default of ' +
                                 '"{}".'.format(self.DEFAULT_RECOMMENDER))
        else:
            # Parse the given recommender names.
            keys = set()
            for a in os.environ[self.ENV_VAR].split(','):
                a = a.strip()
                if a in self.RECOMMENDERS:
                    keys.add(a)
                else:
                    self._logger.warning('Follow recommender "{}" '.format(a) +
                                         'requested, but no such system found. '
                                         'Skipping.')

            if len(keys) == 0:
                # User didn't give any valid names.
                self._logger.warning('No valid values given for follow ' +
                                     'recommender, using default of ' +
                                     '"{}".'.format(self.DEFAULT_RECOMMENDER))
                keys = [self.DEFAULT_RECOMMENDER]
        self._logger.info("Using follow recommenders [" + ', '.join(k for k in keys) + "].")

        # At this point, keys[] should contain either the default system, or
        # a list of user-chosen ones.
        recommenders = []
        for k in keys:
            constructor = self.RECOMMENDERS[k]
            r = constructor(self._logger, self._users_util, self._db_stub)
            recommenders.append(r)
        return recommenders
