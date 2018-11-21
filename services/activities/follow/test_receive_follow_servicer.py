import unittest
from unittest.mock import Mock

from receive_follow_servicer import ReceiveFollowServicer
from services.proto import s2s_follow_pb2
from services.proto import follows_pb2


class ReceiveFollowServicerTest(unittest.TestCase):

    def setUp(self):
        self.servicer = ReceiveFollowServicer(Mock(), Mock(), Mock())
        self.servicer._users_util.parse_actor = lambda x: ('host', 'handle')

    def test_s2s_req_to_follows_req(self):
        req = s2s_follow_pb2.ReceivedFollowDetails()
        req.follower = 'b.com/@a'
        req.followed = 'c.com/@d'
        expected = follows_pb2.ForeignToLocalFollow()
        expected.follower_host = 'host'
        expected.follower_handle = 'handle'
        expected.followed = 'handle'
        self.assertEqual(self.servicer._s2s_req_to_follows_req(req), expected)
