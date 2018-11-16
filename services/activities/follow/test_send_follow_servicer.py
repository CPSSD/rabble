import unittest
from unittest.mock import Mock

from send_follow_servicer import SendFollowServicer
from proto import s2s_follow_pb2

class SendFollowServicerTest(unittest.TestCase):
    def setUp(self):
        self.servicer = SendFollowServicer(Mock())

    def test_build_actor(self):
        self.assertEqual(self.servicer._build_actor('a', 'b.com'),
                         'b.com/@a')

    def test_build_inbox_url(self):
        self.assertEqual(self.servicer._build_inbox_url('a', 'b.com'),
                         'b.com/ap/@a/inbox')

    def test_build_activity(self):
        e = self.servicer._build_activity('FOLLOWER', 'FOLLOWED')
        self.assertEqual(e['@context'],
                         'https://www.w3.org/ns/activitystreams')
        self.assertEqual(e['type'], 'Follow')
        self.assertEqual(e['actor'], 'FOLLOWER')
        self.assertEqual(e['object'], 'FOLLOWED')
        self.assertEqual(e['to'], ['FOLLOWED'])

    def test_SendFollowActivity(self):
        resp = self.servicer.SendFollowActivity(None, None)
        self.assertEqual(resp.result_type, 
                         s2s_follow_pb2.FollowActivityResponse.OK)
