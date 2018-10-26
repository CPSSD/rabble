from posts_servicer import PostsDatabaseServicer
from users_servicer import UsersDatabaseServicer

import database_pb2_grpc


class DatabaseServicer(database_pb2_grpc.DatabaseServicer):

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

        posts_servicer = PostsDatabaseServicer(db, logger)
        self.Posts = posts_servicer.Posts
        users_servicer = UsersDatabaseServicer(db, logger)
        self.Users = users_servicer.Users