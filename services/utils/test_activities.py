import unittest
from unittest.mock import Mock, patch

from utils.activities import ActivitiesUtil


class ActivitiesUtilTest(unittest.TestCase):
    def setUp(self):
        self.activ_util = ActivitiesUtil(Mock(), Mock())

    def test_build_actor(self):
        self.assertEqual(self.activ_util.build_actor('a', 'b.com'),
                         'https://b.com/ap/@a')

    def test_build_inbox_url(self):
        self.assertEqual(self.activ_util.build_inbox_url('a', 'b.com'),
                         'https://b.com/ap/@a/inbox')

    def test_send_activity(self):
        import requests
        requests.Session = Mock()
        activity = {'@context': 'https://test.com', 'data': 'yes'}
        _, e = self.activ_util.send_activity(activity,
                                             'https://followed.com/ap/@b/inbox')
        self.assertIsNone(e)
