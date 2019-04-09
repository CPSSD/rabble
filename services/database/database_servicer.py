from follow_servicer import FollowDatabaseServicer
from posts_servicer import PostsDatabaseServicer
from users_servicer import UsersDatabaseServicer
from like_servicer import LikeDatabaseServicer
from view_servicer import ViewDatabaseServicer
from log_servicer import LogDatabaseServicer
from share_servicer import ShareDatabaseServicer

from services.proto import database_pb2_grpc


class DatabaseServicer(database_pb2_grpc.DatabaseServicer):

    def __init__(self, db, logger):
        self._db = db
        self._logger = logger

        posts_servicer = PostsDatabaseServicer(db, logger)
        self.Posts = posts_servicer.Posts
        self.InstanceFeed = posts_servicer.InstanceFeed
        self.SearchArticles = posts_servicer.SearchArticles
        self.CreatePostsIndex = posts_servicer.CreatePostsIndex
        self.RandomPosts = posts_servicer.RandomPosts
        self.SafeRemovePost = posts_servicer.SafeRemovePost
        users_servicer = UsersDatabaseServicer(db, logger)
        self.Users = users_servicer.Users
        self.SearchUsers = users_servicer.SearchUsers
        self.PendingFollows = users_servicer.PendingFollows
        self.CreateUsersIndex = users_servicer.CreateUsersIndex
        follow_servicer = FollowDatabaseServicer(db, logger)
        self.Follow = follow_servicer.Follow
        like_servicer = LikeDatabaseServicer(db, logger)
        self.AddLike = like_servicer.AddLike
        self.RemoveLike = like_servicer.RemoveLike
        self.LikedCollection = like_servicer.LikedCollection
        view_servicer = ViewDatabaseServicer(db, logger)
        self.AddView = view_servicer.AddView
        log_servicer = LogDatabaseServicer(db, logger)
        self.AddLog = log_servicer.AddLog
        self.AllUsers = users_servicer.AllUsers
        share_servicer = ShareDatabaseServicer(db, logger)
        self.AddShare = share_servicer.AddShare
        self.FindShare = share_servicer.FindShare
        self.SharedPosts = share_servicer.SharedPosts
