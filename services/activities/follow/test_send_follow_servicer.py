import unittest
from unittest.mock import Mock

from send_follow_servicer import SendFollowServicer
from proto import s2s_follow_pb2

class SendFollowServicerTest(unittest.TestCase):
    def setUp(self):
        self.servicer = SendFollowServicer(Mock())

    def test_SendFollowActivity(self):
        resp = self.servicer.SendFollowActivity(None, None)
        self.assertEqual(resp.result_type, 
                         s2s_follow_pb2.FollowActivityResponse.OK)
