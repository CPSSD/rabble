import unittest
import os
from unittest.mock import Mock

from send_unfollow import SendUnfollowServicer
from test_receive_follow import FakeDatabase
from services.proto import follows_pb2
from services.proto import database_pb2


class SendUnfollowTest(unittest.TestCase):

    def setUp(self):
        os.environ["HOST_NAME"] = "cianisharrypotter.secret"
        self.db = FakeDatabase()
        util = Mock()
        user_util = Mock()
        database_stub = Mock()
        util.create_follow_in_db = self.db.add_follow
        user_util.get_user_from_db = self.db.get_user
        user_util.get_or_create_user_from_db = self.db.get_or_create_user
        user_util.parse_username = self.db.parse_username
        database_stub.Follow = self.db.Follow
        s2s_stub = Mock()
        self.servicer = SendUnfollowServicer(Mock(),
                                             util,
                                             user_util,
                                             database_stub,
                                             s2s_stub,
                                             Mock())

    def tearDown(self):
        del os.environ["HOST_NAME"]

    def test_good_request(self):
        req = follows_pb2.LocalToAnyFollow(
            follower="tom@rabble.cat",
            followed="jerry@mouse.house",
        )
        res = self.servicer.SendUnfollow(req, Mock())
        self.assertEqual(res.result_type, follows_pb2.FollowResponse.OK)
        self.assertIsNotNone(self.db.follow_called_with)
        self.db.reset()

    def test_errors_when_empty_request(self):
        req = follows_pb2.LocalToAnyFollow()
        res = self.servicer.SendUnfollow(req, Mock())
        self.assertEqual(res.result_type, follows_pb2.FollowResponse.ERROR)
        self.assertIsNone(self.db.follow_called_with)
        self.db.reset()
