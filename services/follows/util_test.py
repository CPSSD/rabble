import logging
import unittest

from util import Util


class UtilTest(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.util = Util(self.logger)

    def test_parse_local_username(self):
        a, b = self.util.parse_username('admin')
        self.assertEqual(a, 'admin')
        self.assertIsNone(b)

    def test_parse_foreign_username(self):
        a, b = self.util.parse_username('cianlr@neopets.com')
        self.assertEqual(a, 'cianlr')
        self.assertEqual(b, 'neopets.com')

    def test_parse_prefixed_local_username(self):
        a, b = self.util.parse_username('@admin')
        self.assertEqual(a, 'admin')
        self.assertIsNone(b)

    def test_parse_prefixed_foreign_username(self):
        a, b = self.util.parse_username('@cianlr@neopets.com')
        self.assertEqual(a, 'cianlr')
        self.assertEqual(b, 'neopets.com')

    def test_parse_bad_username(self):
        with self.assertLogs(self.logger, level='WARNING'):
            a, b = self.util.parse_username('a@b@c')
            self.assertIsNone(a)
            self.assertIsNone(b)

    def test_get_user_from_db_too_many_attempts(self):
        resp = self.util.get_user_from_db(None, None, attempt_number=100)
        self.assertIsNone(resp)


if __name__ == '__main__':
    unittest.main()
