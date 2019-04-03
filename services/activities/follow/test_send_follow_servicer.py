import unittest
from unittest.mock import Mock, patch

from send_follow_servicer import SendFollowServicer
from services.proto import s2s_follow_pb2
from utils.activities import ActivitiesUtil


class SendFollowServicerTest(unittest.TestCase):

    def setUp(self):
        self.activ_util = ActivitiesUtil(Mock(), Mock())
        self.activ_util._get_activitypub_actor_url = lambda host, handle: (host + '/ap/@' + handle)
        self.activ_util.build_inbox_url = lambda handle, host: (host + '/ap/@' + handle + '/inbox')
        self.servicer = SendFollowServicer(Mock(), self.activ_util, Mock())
        self.mock_response = Mock()
        self.mock_response.text = '{"success": true, "error": ""}'

    def test_build_activity(self):
        e = self.servicer._build_activity('FOLLOWER', 'FOLLOWED')
        self.assertEqual(e['@context'],
                         ActivitiesUtil.rabble_context())
        self.assertEqual(e['type'], 'Follow')
        self.assertEqual(e['actor'], 'FOLLOWER')
        self.assertEqual(e['object'], 'FOLLOWED')
        self.assertEqual(e['to'], ['FOLLOWED'])

    def test_SendFollowActivity(self):
        with patch(__name__ + '.ActivitiesUtil.send_activity') as mock_send:
            mock_send.return_value = (self.mock_response, None)
            req = s2s_follow_pb2.FollowDetails()
            req.follower.host = 'follower.com'
            req.follower.handle = 'a'
            req.followed.host = 'followed.com'
            req.followed.handle = 'b'
            resp = self.servicer.SendFollowActivity(req, None)
            self.assertEqual(resp.result_type,
                             s2s_follow_pb2.FollowActivityResponse.OK)
            self.assertEqual(resp.error, '')
            expected = self.servicer._build_activity('https://follower.com/ap/@a',
                                                     'https://followed.com/ap/@b')
            mock_send.assert_called_once_with(expected,
                                              'https://followed.com/ap/@b/inbox')

    def test_SendFollowActivity_foreign_error(self):
        self.mock_response.text = '{"success": false, "error": "Some Error"}'
        with patch(__name__ + '.ActivitiesUtil.send_activity') as mock_send:
            mock_send.return_value = (self.mock_response, None)
            req = s2s_follow_pb2.FollowDetails()
            req.follower.host = 'follower.com'
            req.follower.handle = 'a'
            req.followed.host = 'followed.com'
            req.followed.handle = 'b'
            resp = self.servicer.SendFollowActivity(req, None)
            self.assertEqual(resp.result_type,
                             s2s_follow_pb2.FollowActivityResponse.ERROR)
            expected = self.servicer._build_activity('https://follower.com/ap/@a',
                                                     'https://followed.com/ap/@b')
            mock_send.assert_called_once_with(expected,
                                              'https://followed.com/ap/@b/inbox')

    def test_SendFollowActivity_json_error(self):
        self.mock_response.text = "{invalid-json}}}}"
        with patch(__name__ + '.ActivitiesUtil.send_activity') as mock_send:
            mock_send.return_value = (self.mock_response, None)
            req = s2s_follow_pb2.FollowDetails()
            req.follower.host = 'follower.com'
            req.follower.handle = 'a'
            req.followed.host = 'followed.com'
            req.followed.handle = 'b'
            resp = self.servicer.SendFollowActivity(req, None)
            self.assertEqual(resp.result_type,
                             s2s_follow_pb2.FollowActivityResponse.ERROR)
            expected = self.servicer._build_activity('https://follower.com/ap/@a',
                                                     'https://followed.com/ap/@b')
            mock_send.assert_called_once_with(expected,
                                              'https://followed.com/ap/@b/inbox')

    def test_SendFollowActivity_return_error(self):
        with patch(__name__ + '.ActivitiesUtil.send_activity') as mock_send:
            mock_send.return_value = (None, 'insert error here')
            req = s2s_follow_pb2.FollowDetails()
            req.follower.host = 'follower.com'
            req.follower.handle = 'a'
            req.followed.host = 'followed.com'
            req.followed.handle = 'b'
            resp = self.servicer.SendFollowActivity(req, None)
            self.assertEqual(resp.result_type,
                             s2s_follow_pb2.FollowActivityResponse.ERROR)
            self.assertEqual(resp.error, 'insert error here')
            expected = self.servicer._build_activity('https://follower.com/ap/@a',
                                                     'https://followed.com/ap/@b')
            mock_send.assert_called_once_with(expected,
                                              'https://followed.com/ap/@b/inbox')
