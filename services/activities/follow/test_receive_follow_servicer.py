import unittest
from unittest.mock import Mock

from receive_follow_servicer import ReceiveFollowServicer
from proto import s2s_follow_pb2

class ReceiveFollowServicerTest(unittest.TestCase):
    def setUp(self):
        self.servicer = ReceiveFollowServicer(Mock())

    def test_ReceiveFollowActivity(self):
        resp = self.servicer.ReceiveFollowActivity(None, None)
        self.assertEqual(resp.result_type, 
                         s2s_follow_pb2.FollowActivityResponse.OK)
