from enum import Enum

from services.proto import database_pb2
from services.proto import recommend_follows_pb2


class GetFollowRecommendationsServicer:

    def __init__(self, logger, users_util, database_stub):
        self._logger = logger
        self._users_util = users_util
        self._database_stub = database_stub

    def GetFollowRecommendations(self, request, context):
        self._logger.debug('GetFollowing, username = %s', request.username)
        return None
