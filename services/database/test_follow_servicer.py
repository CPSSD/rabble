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

    def add_follow(self, follower=None, followed=None, state=None):
        follow_entry = database_pb2.Follow(
            follower=follower,
            followed=followed,
            state=state,
        )

        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.INSERT,
            entry=follow_entry,
        )

        add_res = self.service.Follow(req, self.ctx)
        self.assertNotEqual(add_res.result_type,
                            database_pb2.DbFollowResponse.ERROR)
        return add_res


    def find_follow(self, follower=None, followed=None, state=None):
        follow_entry = database_pb2.Follow(
            follower=follower,
            followed=followed,
            state=state,
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
            state=database_pb2.Follow.ACTIVE
        )
        self.assertEqual(len(find_res.results), 1)
        self.assertIn(want, find_res.results)

    def test_insert_and_find_state_follow(self):
        self.add_follow(follower=3,
                        followed=4,
                        state=database_pb2.Follow.PENDING)
        find_res = self.find_follow(followed=4,
                                    state=database_pb2.Follow.PENDING)
        want = database_pb2.Follow(follower=3,
                                   followed=4,
                                   state=database_pb2.Follow.PENDING)
        self.assertEqual(len(find_res.results), 1)
        self.assertIn(want, find_res.results)

    def test_multiple_follows(self):
        self.add_follow(follower=10, followed=14)
        self.add_follow(follower=11, followed=14)
        self.add_follow(follower=12,
                        followed=14,
                        state=database_pb2.Follow.PENDING)
        find_res = self.find_follow(followed=14)
        want_in = [
                database_pb2.Follow(follower=10,
                                    followed=14,
                                    state=database_pb2.Follow.ACTIVE),
                database_pb2.Follow(follower=11,
                                    followed=14,
                                    state=database_pb2.Follow.ACTIVE),
        ]
        self.assertEqual(len(find_res.results), 2)
        self.assertIn(want_in[0], find_res.results)
        self.assertIn(want_in[1], find_res.results)

    def test_find_rejected(self):
        self.add_follow(follower=100, followed=140)
        self.add_follow(follower=110, followed=140)
        self.add_follow(follower=120,
                        followed=140,
                        state=database_pb2.Follow.PENDING)
        self.add_follow(follower=130,
                        followed=140,
                        state=database_pb2.Follow.REJECTED)
        find_res = self.find_follow(followed=140,
                                    state=database_pb2.Follow.REJECTED)
        want = database_pb2.Follow(follower=130,
                                   followed=140,
                                   state=database_pb2.Follow.REJECTED)
        self.assertIn(want, find_res.results)
        self.assertEqual(len(find_res.results), 1)


class FollowFindAllDatabase(FollowDatabaseHelper):
    # This test is located in another test that uses a fresh database.
    # That way we don't rely on state set by another test.
    def test_find_all(self):
        self.add_follow(follower=1, followed=20)
        self.add_follow(follower=1, followed=15)
        self.add_follow(follower=2, followed=16)
        self.add_follow(follower=3,
                        followed=20,
                        state=database_pb2.Follow.PENDING)
        self.add_follow(follower=4,
                        followed=15,
                        state=database_pb2.Follow.REJECTED)
        do_not_want = [
                database_pb2.Follow(follower=3,
                                    followed=20,
                                    state=database_pb2.Follow.PENDING,
                ),
                database_pb2.Follow(follower=4,
                                    followed=15,
                                    state=database_pb2.Follow.REJECTED,
                ),
        ]

        find_res = self.find_follow()
        self.assertNotIn(do_not_want[0], find_res.results)
        self.assertNotIn(do_not_want[1], find_res.results)
        self.assertEqual(len(find_res.results), 3)
