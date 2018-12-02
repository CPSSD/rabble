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
        return database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[
                database_pb2.UsersEntry(
                    global_id=456,
                    handle="minecraft4ever",
                    host="rabble.mojang.com",
                    display_name="Minecraft4Ever",
                )
            ],
        )


class SendLikeServicerTest(unittest.TestCase):
    def setUp(self):
        self.activ_util = ActivitiesUtil(Mock())
        self.db = MockDB()
        self.users_util = UsersUtil(Mock(), self.db)
        self.servicer = SendLikeServicer(
            Mock(), self.db, self.users_util, self.activ_util, "localhost")
        self.data = None
        self.url = None
        self.activ_util.send_activity = self.save_request

    def save_request(self, data, url):
        self.data = data
        self.url = url
        return "my_response", None

    def test_SendLikeActivity(self):
        req = like_pb2.LikeDetails(
            article_id=123,
            liker_handle="farmlover73",
        )
        resp = self.servicer.SendLikeActivity(req, None)
        self.assertEqual(resp.result_type, like_pb2.LikeResponse.OK)
        # Check that the request sent makes sense.
        self.assertEqual(self.data["type"], "Like")
        self.assertEqual(self.data["actor"]["handle"], "farmlover73")
        self.assertEqual(self.data["object"]["title"], "Minecraft Farming 101")
        self.assertIn("rabble.mojang.com", self.url)
        self.assertIn("@minecraft4ever", self.url)
    
    def test_SendLikeActivitySendingError(self):
        req = like_pb2.LikeDetails(
            article_id=123,
            liker_handle="farmlover73",
        )
        self.activ_util.send_activity = lambda *_: ("", "Error 404")
        resp = self.servicer.SendLikeActivity(req, None)
        self.assertEqual(resp.result_type, like_pb2.LikeResponse.ERROR)
    
    def test_SendLikeActivityNoArticle(self):
        req = like_pb2.LikeDetails(
            article_id=123,
            liker_handle="farmlover73",
        )
        self.db.Posts = lambda *_: database_pb2.PostsResponse(
            result_type=database_pb2.PostsResponse.OK,
            results=[],
        )
        resp = self.servicer.SendLikeActivity(req, None)
        self.assertEqual(resp.result_type, like_pb2.LikeResponse.ERROR)

