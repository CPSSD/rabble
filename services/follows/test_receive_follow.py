import unittest
import os
from unittest.mock import Mock

from receive_follow import ReceiveFollowServicer
from services.proto import follows_pb2
from services.proto import database_pb2

class FakeDatabase:
    def __init__(self):
        self.users_dict = {
                ('exists', None): 1,
                ('also_exists', None): 2,
        }
        self.current_id = 2
        self.reset()

    def reset(self):
        # Since we're directly hooking in functions into the test, we cant
        # use mock.assert_called_with, because of that, we'll record what
        # we were called with manually. It's not the prettiest solution :(
        self.get_user_called_with = None
        self.get_or_create_user_called_with = None
        self.add_follow_called_with = None

    def lookup_user(self, user):
        if user not in self.users_dict:
            return None
        return database_pb2.UsersEntry(global_id = self.users_dict[user])

    def get_user(self, handle=None, host=None):
        self.get_user_called_with = (handle, host)
        if handle == None:
            return None
        return self.lookup_user((handle, host))

    def get_or_create_user(self, handle=None, host=None):
        # we should never be creating local users here, so we check that here.
        self.get_or_create_user_called_with = (handle, host)
        if handle == None or host == None:
            return None
        user = (handle, host)
        self.current_id += 1
        self.users_dict[user] = self.current_id
        return self.lookup_user(user)

    def add_follow(self, foriegn, local):
        self.add_follow_called_with = (foriegn, local)
        resp = database_pb2.DbFollowResponse()
        ids = set(self.users_dict.values())
        if foriegn not in ids or local not in ids:
            resp.result_type = database_pb2.DbFollowResponse.ERROR
            return resp 
        resp.result_type = database_pb2.DbFollowResponse.OK
        return resp


class ReceiveFollowTest(unittest.TestCase):
    def setUp(self):
        os.environ["HOST_NAME"] = "cianisharrypotter.secret"
        self.db = FakeDatabase()
        util = Mock()
        user_util = Mock()
        util.create_follow_in_db = self.db.add_follow
        user_util.get_user_from_db = self.db.get_user
        user_util.get_or_create_user_from_db = self.db.get_or_create_user
        # TODO(devoxel): Test approver interactions
        self.servicer = ReceiveFollowServicer(Mock(),
                                              util,
                                              user_util,
                                              Mock(),
                                              Mock())

    def tearDown(self):
        del os.environ["HOST_NAME"]

    def test_good_request(self):
        req = follows_pb2.ForeignToLocalFollow(
            follower_host = 'http://whatever.com',
            follower_handle = 'jim_pickens',
            followed = 'exists',
        )
        res = self.servicer.ReceiveFollowRequest(req, Mock())
        self.assertEqual(res.result_type, follows_pb2.FollowResponse.OK)
        self.assertIsNotNone(self.db.add_follow_called_with)
        self.db.reset()

    def test_errors_when_local_user_does_not_exist(self):
        req = follows_pb2.ForeignToLocalFollow(
            follower_host = 'http://whatever.com',
            follower_handle = 'jim_pickens',
            followed = 'bore_ragnarock',
        )
        res = self.servicer.ReceiveFollowRequest(req, Mock())
        self.assertEqual(res.result_type, follows_pb2.FollowResponse.ERROR)
        self.assertIn('bore_ragnarock', res.error)
        self.assertIsNone(self.db.add_follow_called_with)
        self.db.reset()

    def test_errors_when_empty_request(self):
        req = follows_pb2.ForeignToLocalFollow()
        res = self.servicer.ReceiveFollowRequest(req, Mock())
        self.assertEqual(res.result_type, follows_pb2.FollowResponse.ERROR)
        self.assertIsNone(self.db.add_follow_called_with)
        self.db.reset()

    def test_errors_when_bad_host(self):
        req = follows_pb2.ForeignToLocalFollow(
            follower_handle = 'jim_pickens',
            followed = 'bore_ragnarock',
        )
        res = self.servicer.ReceiveFollowRequest(req, Mock())
        self.assertEqual(res.result_type, follows_pb2.FollowResponse.ERROR)
        self.assertIn('No host', res.error)
        self.assertIsNone(self.db.add_follow_called_with)
        self.db.reset()
