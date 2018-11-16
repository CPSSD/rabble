import logging
import unittest

from users import UsersUtil


class UsersUtilTest(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.util = UsersUtil(self.logger, None)

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

    def test_parse_actor(self):
        a, b = self.util.parse_actor('neopets.com/@cianlr')
        self.assertEqual(a, 'neopets.com')
        self.assertEqual(b, 'cianlr')

    def test_parse_bad_actor(self):
        with self.assertLogs(self.logger, level='WARNING'):
            a, b = self.util.parse_actor('a@b@c')
            self.assertIsNone(a)
            self.assertIsNone(b)

    def test_parse_bad_username(self):
        with self.assertLogs(self.logger, level='WARNING'):
            a, b = self.util.parse_username('a@b@c')
            self.assertIsNone(a)
            self.assertIsNone(b)

    def test_get_or_create_user_from_db_too_many_attempts(self):
        resp = self.util.get_or_create_user_from_db(None, None, attempt_number=100)
        self.assertIsNone(resp)


if __name__ == '__main__':
    unittest.main()
