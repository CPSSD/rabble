import unittest
import logging
import os

import posts_servicer
import users_servicer
import like_servicer
import follow_servicer
import database
from services.proto import database_pb2

USERS_DB_PATH = "./testdb/users.db"


class UsersDatabaseHelper(unittest.TestCase):

    def setUp(self):
        def clean_database():
            os.remove(USERS_DB_PATH)

        def fake_context():
            def called():
                raise NotImplemented
            return called

        logger = logging.getLogger()
        self.db = database.build_database(logger,
                                          "rabble_schema.sql",
                                          USERS_DB_PATH)
        self.addCleanup(clean_database)
        self.posts = posts_servicer.PostsDatabaseServicer(self.db, logger)
        self.users = users_servicer.UsersDatabaseServicer(self.db, logger)
        self.like = like_servicer.LikeDatabaseServicer(self.db, logger)
        self.follow = follow_servicer.FollowDatabaseServicer(self.db, logger)
        self.ctx = fake_context()

    def add_user(self, handle=None, host=None):
        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
            host_is_null=(host is None),
        )

        req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.INSERT,
            entry=user_entry,
        )
        add_res = self.users.Users(req, self.ctx)
        self.assertNotEqual(add_res.result_type,
                            database_pb2.UsersResponse.ERROR)
        return add_res

    def all_users(self):
        req = database_pb2.AllUsersRequest()
        res = self.users.AllUsers(req, self.ctx)
        print(res.error)
        self.assertNotEqual(res.result_type, database_pb2.UsersResponse.ERROR)
        return res

class UsersDatabase(UsersDatabaseHelper):

    def test_all_users_when_no_users(self):
        res = self.all_users()
        want = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[]
        )
        self.assertEqual(want, res)

    def test_all_users(self):
        res = self.all_users()
        self.assertEqual(0, len(res.results))
        self.add_user(handle='mao_zedong', host='cpc.cn')
        self.add_user(handle='chiang_kai_shek', host='kuomintang.tw')
        self.add_user(handle='gerry adams', host=None)
        res = self.all_users()
        self.assertEqual(3, len(res.results))
