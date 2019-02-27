import unittest
from unittest.mock import Mock, patch

from utils.activities import ActivitiesUtil


class ActivitiesUtilTest(unittest.TestCase):
    def setUp(self):
        self.activ_util = ActivitiesUtil(Mock())

    def test_build_actor(self):
        self.assertEqual(self.activ_util.build_actor('a', 'b.com'),
                         'http://b.com/ap/@a')

    def test_build_inbox_url(self):
        self.assertEqual(self.activ_util.build_inbox_url('a', 'b.com'),
                         'http://b.com/ap/@a/inbox')

    def test_send_activity_error(self):
        from urllib import request
        request.Request = Mock()
        request.urlopen = Mock()
        request.urlopen.side_effect = Exception('some weird error')
        activity = {'@context': 'http://test.com', 'data': 'yes'}
        _, e = self.activ_util.send_activity(activity,
                                             'followed.com/ap/@b/inbox')
        self.assertEqual(e, 'some weird error')

    def test_send_activity(self):
        from urllib import request
        request.Request = Mock()
        request.urlopen = Mock()
        activity = {'@context': 'http://test.com', 'data': 'yes'}
        _, e = self.activ_util.send_activity(activity,
                                             'followed.com/ap/@b/inbox')
        self.assertIsNone(e)
