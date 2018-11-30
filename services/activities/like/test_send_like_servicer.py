import unittest
from unittest.mock import Mock, patch

from send_like_servicer import SendLikeServicer
from services.proto import like_pb2
from services.proto import database_pb2
from utils.activities import ActivitiesUtil
from utils.users import UsersUtil


class MockDB:
    def Posts(*args):
        return database_pb2.PostsResponse(
            result_type=database_pb2.PostsResponse.OK,
            results=[
                database_pb2.PostsEntry(
                    global_id=123,
                    author_id=456,
                    title="Minecraft Farming 101",
                    body="Don't bother",
                )
            ]
        )

    def Users(*args):
        print(args)


class SendLikeServicerTest(unittest.TestCase):
    def setUp(self):
        self.activ_util = ActivitiesUtil(Mock())
        self.db = MockDB()
        self.users_util = UsersUtil(Mock(), self.db)
        self.servicer = SendLikeServicer(
            Mock(), self.db, self.users_util, self.activ_util)

    def test_SendLikeActivity(self):
        req = like_pb2.LikeDetails(
            article_id=123,
            liker_host="myhost.com",
            liker_handle="farmlover73",
        )
        resp = self.servicer.SendLikeActivity(req, None)
        self.assertEq(resp.result_type, like_pb2.LikeResponse.OK)

    #def test_SendFollowActivity(self):
    #    with patch(__name__ + '.ActivitiesUtil.send_activity') as mock_send:
    #        mock_send.return_value = ("response", None)
    #        req = s2s_follow_pb2.FollowDetails()
    #        req.follower.host = 'follower.com'
    #        req.follower.handle = 'a'
    #        req.followed.host = 'followed.com'
    #        req.followed.handle = 'b'
    #        resp = self.servicer.SendFollowActivity(req, None)
    #        self.assertEqual(resp.result_type,
    #                         s2s_follow_pb2.FollowActivityResponse.OK)
    #        self.assertEqual(resp.error, '')
    #        expected = self.servicer._build_activity('http://follower.com/@a',
    #                                                 'http://followed.com/@b')
    #        mock_send.assert_called_once_with(expected,
    #                                          'http://followed.com/ap/@b/inbox')

    #def test_SendFollowActivity_return_error(self):
    #    with patch(__name__ + '.ActivitiesUtil.send_activity') as mock_send:
    #        mock_send.return_value = (None, 'insert error here')
    #        req = s2s_follow_pb2.FollowDetails()
    #        req.follower.host = 'follower.com'
    #        req.follower.handle = 'a'
    #        req.followed.host = 'followed.com'
    #        req.followed.handle = 'b'
    #        resp = self.servicer.SendFollowActivity(req, None)
    #        self.assertEqual(resp.result_type,
    #                         s2s_follow_pb2.FollowActivityResponse.ERROR)
    #        self.assertEqual(resp.error, 'insert error here')
    #        expected = self.servicer._build_activity('http://follower.com/@a',
    #                                                 'http://followed.com/@b')
    #        mock_send.assert_called_once_with(expected,
    #                                          'http://followed.com/ap/@b/inbox')
