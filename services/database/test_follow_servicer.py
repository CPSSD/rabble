import unittest
import logging
import os
from functools import partial

import follow_servicer
import database
from services.proto import database_pb2

FOLLOW_DB_PATH = "./testdb/follow.db"

class FollowDatabaseHelper(unittest.TestCase):
    def setUp(self):
        def clean_database():
            os.remove(FOLLOW_DB_PATH)

        def fake_context():
            def called():
                raise NotImplemented
            return called

        logger = logging.getLogger()
        self.db = database.build_database(logger,
                                          "rabble_schema.sql",
                                          FOLLOW_DB_PATH)
        self.addCleanup(clean_database)
        self.service = follow_servicer.FollowDatabaseServicer(self.db, logger)
        self.ctx = fake_context()

    def add_follow(self, follower=None, followed=None, intermediate=None):
        follow_entry = database_pb2.Follow(
            follower=follower,
            followed=followed,
            intermediate=intermediate,
        )

        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.INSERT,
            entry=follow_entry,
        )

        add_res = self.service.Follow(req, self.ctx)
        self.assertNotEqual(add_res.result_type,
                            database_pb2.DbFollowResponse.ERROR)
        return add_res


    def find_follow(self, follower=None, followed=None, intermediate=None):
        follow_entry = database_pb2.Follow(
            follower=follower,
            followed=followed,
            intermediate=intermediate,
        )

        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry,
        )

        find_res = self.service.Follow(req, self.ctx)
        self.assertNotEqual(find_res.result_type,
                            database_pb2.DbFollowResponse.ERROR)
        return find_res



class FollowDatabase(FollowDatabaseHelper):
    def test_insert_and_find_follow(self):
        self.add_follow(follower=1, followed=2)
        find_res = self.find_follow(followed=2)
        want = database_pb2.Follow(
            follower=1,
            followed=2,
            intermediate=False
        )
        self.assertEqual(len(find_res.results), 1)
        self.assertIn(want, find_res.results)

    def test_insert_and_find_intermediate_follow(self):
        self.add_follow(follower=3, followed=4, intermediate=True)
        find_res = self.find_follow(followed=4, intermediate=True)
        want = database_pb2.Follow(
            follower=3,
            followed=4,
            intermediate=True,
        )
        self.assertEqual(len(find_res.results), 1)
        self.assertIn(want, find_res.results)

    def test_multiple_follows(self):
        self.add_follow(follower=10, followed=14)
        self.add_follow(follower=11, followed=14)
        self.add_follow(follower=12, followed=14, intermediate=True)
        find_res = self.find_follow(followed=14)

        want_in = [
                database_pb2.Follow(follower=10,
                                    followed=14,
                                    intermediate=False),
                database_pb2.Follow(follower=11,
                                    followed=14,
                                    intermediate=False),
        ]

        self.assertEqual(len(find_res.results), 2)
        self.assertIn(want_in[0], find_res.results)
        self.assertIn(want_in[1], find_res.results)

class FollowFindAllDatabase(FollowDatabaseHelper):
    # This test is located in another test that uses a fresh database.
    # That way we don't rely on state set by another test.
    def test_find_all(self):
        self.add_follow(follower=10, followed=14)
        self.add_follow(follower=11, followed=14)
        self.add_follow(follower=18, followed=19, intermediate=True)
        do_not_want = database_pb2.Follow(
                follower=18,
                followed=19,
                intermediate=True,
        )
        find_res = self.find_follow()
        self.assertNotIn(do_not_want, find_res.results)
        self.assertEqual(len(find_res.results), 2)
