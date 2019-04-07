import unittest
from unittest.mock import Mock, patch

from send_like_servicer import SendLikeServicer
from services.proto import like_pb2
from services.proto import database_pb2
from utils.activities import ActivitiesUtil
from utils.users import UsersUtil


class MockDB:
    def __init__(self):
        self.posts_response = database_pb2.PostsResponse(
            result_type=database_pb2.PostsResponse.OK,
            results=[
                database_pb2.PostsEntry(
                    global_id=123,
                    author_id=456,
                    title="Minecraft Farming 101",
                    body="Don't bother",
                    ap_id="https://rabble.mojang.com/ap/@minecraft4ever/666",
                )
            ]
        )
        self.users_response = database_pb2.UsersResponse(
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

    def Posts(self, *args):
        return self.posts_response

    def Users(self, *args):
        return self.users_response


class SendLikeServicerTest(unittest.TestCase):
    def setUp(self):
        self.db = MockDB()
        self.activ_util = ActivitiesUtil(Mock(), self.db)
        self.activ_util.build_actor = lambda han, host: f'{host}/ap/@{han}'
        self.activ_util.build_inbox_url = lambda han, host: f'{host}/ap/@{han}/inbox'
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
        self.assertEqual(self.data["actor"]["type"], "Person")
        self.assertIn("localhost/ap/@farmlover73", self.data["actor"]["id"])
        # Check the object is the article URL.
        self.assertEqual("https://rabble.mojang.com/ap/@minecraft4ever/666",
                         self.data["object"])
        # Check the request was sent to a valid URL.
        self.assertIn("rabble.mojang.com", self.url)
        self.assertIn("@minecraft4ever", self.url)

    def test_SendLikeActivityLocal(self):
        req = like_pb2.LikeDetails(
            article_id=123,
            liker_handle="farmlover73",
        )
        # Simulate local user.
        self.db.posts_response.results[0].ClearField('ap_id')
        self.db.users_response.results[0].ClearField('host')
        resp = self.servicer.SendLikeActivity(req, None)
        self.assertEqual(resp.result_type, like_pb2.LikeResponse.OK)
        # Check that the request sent makes sense.
        self.assertEqual(self.data["type"], "Like")
        self.assertEqual(self.data["actor"]["type"], "Person")
        self.assertIn("localhost/ap/@farmlover73", self.data["actor"]["id"])
        # Check the object is the article URL.
        self.assertEqual("http://localhost/ap/@minecraft4ever/123",
                         self.data["object"])
        # TODO(CianLR): Check that the article ID is in the object.
        # Check the request was sent to a valid URL.
        self.assertIn("localhost", self.url)
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
