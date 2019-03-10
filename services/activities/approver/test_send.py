import unittest
from unittest.mock import Mock

from send import SendApprovalServicer
from services.proto import approver_pb2
from services.proto import s2s_follow_pb2
from utils.activities import ActivitiesUtil

example_req = approver_pb2.Approval(
    accept=True,
    follow=s2s_follow_pb2.FollowDetails(
        follower=s2s_follow_pb2.FollowActivityUser(
            handle="rtgame",
            host="youtube.com",
        ),
        followed=s2s_follow_pb2.FollowActivityUser(
            handle="callmekevin",
            host="example.com",
        ),
    )
)


class SendServicerTest(unittest.TestCase):

    def setUp(self):
        activ_util = ActivitiesUtil(Mock(), Mock())
        activ_util.send_activity = Mock(return_value=(None, None))
        self.servicer = SendApprovalServicer(Mock(), activ_util)

    def test_build_accept_activity(self):
        req = example_req
        req.accept = True
        want = {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': 'accept',
            'actor': 'http://example.com/@callmekevin',
            'object': {
                'type': 'Follow',
                'actor': 'http://youtube.com/@rtgame',
                'object': 'http://example.com/@callmekevin',
            },
            'to': ['http://youtube.com/@rtgame'],
        }
        self.assertEqual(self.servicer._build_activity(req), want)

    def test_build_reject_activity(self):
        req = example_req
        req.accept = False
        want = {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': 'reject',
            'actor': 'http://example.com/@callmekevin',
            'object': {
                'type': 'Follow',
                'actor': 'http://youtube.com/@rtgame',
                'object': 'http://example.com/@callmekevin',
            },
            'to': ['http://youtube.com/@rtgame'],
        }
        self.assertEqual(self.servicer._build_activity(req), want)
