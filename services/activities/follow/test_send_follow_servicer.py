import unittest
from unittest.mock import Mock, patch

from send_follow_servicer import SendFollowServicer
from services.proto import s2s_follow_pb2


class SendFollowServicerTest(unittest.TestCase):

    def setUp(self):
        self.servicer = SendFollowServicer(Mock())

    def test_build_actor(self):
        self.assertEqual(self.servicer._build_actor('a', 'b.com'),
                         'http://b.com/@a')

    def test_build_inbox_url(self):
        self.assertEqual(self.servicer._build_inbox_url('a', 'b.com'),
                         'http://b.com/ap/@a/inbox')

    def test_build_activity(self):
        e = self.servicer._build_activity('FOLLOWER', 'FOLLOWED')
        self.assertEqual(e['@context'],
                         'https://www.w3.org/ns/activitystreams')
        self.assertEqual(e['type'], 'Follow')
        self.assertEqual(e['actor'], 'FOLLOWER')
        self.assertEqual(e['object'], 'FOLLOWED')
        self.assertEqual(e['to'], ['FOLLOWED'])

    def test_send_activity_error(self):
        from urllib import request
        request.Request = Mock()
        request.urlopen = Mock()
        request.urlopen.side_effect = Exception('some weird error')
        activity = self.servicer._build_activity('FOLLOWER', 'FOLLOWED')
        e = self.servicer._send_activity(activity,
                                         'followed.com/ap/@b/inbox')
        self.assertEqual(e, 'some weird error')

    def test_send_activity(self):
        from urllib import request
        request.Request = Mock()
        request.urlopen = Mock()
        activity = self.servicer._build_activity('FOLLOWER', 'FOLLOWED')
        e = self.servicer._send_activity(activity,
                                         'followed.com/ap/@b/inbox')
        self.assertIsNone(e)

    def test_SendFollowActivity(self):
        with patch(__name__ + '.SendFollowServicer._send_activity') as mock_send:
            mock_send.return_value = None
            req = s2s_follow_pb2.FollowDetails()
            req.follower.host = 'follower.com'
            req.follower.handle = 'a'
            req.followed.host = 'followed.com'
            req.followed.handle = 'b'
            resp = self.servicer.SendFollowActivity(req, None)
            self.assertEqual(resp.result_type,
                             s2s_follow_pb2.FollowActivityResponse.OK)
            self.assertEqual(resp.error, '')
            expected = self.servicer._build_activity('http://follower.com/@a',
                                                     'http://followed.com/@b')
            mock_send.assert_called_once_with(expected,
                                              'http://followed.com/ap/@b/inbox')

    def test_SendFollowActivity_return_error(self):
        with patch(__name__ + '.SendFollowServicer._send_activity') as mock_send:
            mock_send.return_value = 'insert error here'
            req = s2s_follow_pb2.FollowDetails()
            req.follower.host = 'follower.com'
            req.follower.handle = 'a'
            req.followed.host = 'followed.com'
            req.followed.handle = 'b'
            resp = self.servicer.SendFollowActivity(req, None)
            self.assertEqual(resp.result_type,
                             s2s_follow_pb2.FollowActivityResponse.ERROR)
            self.assertEqual(resp.error, 'insert error here')
            expected = self.servicer._build_activity('http://follower.com/@a',
                                                     'http://followed.com/@b')
            mock_send.assert_called_once_with(expected,
                                              'http://followed.com/ap/@b/inbox')
