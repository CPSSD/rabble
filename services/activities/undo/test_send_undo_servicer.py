import unittest
from unittest.mock import Mock, patch

from send_undo_servicer import SendLikeUndoServicer
from services.proto import database_pb2 as dbpb
from services.proto import undo_pb2 as upb
from utils.activities import ActivitiesUtil
from utils.users import UsersUtil


class MockDB:
    def __init__(self):
        self.posts_response = dbpb.PostsResponse(
            result_type=dbpb.PostsResponse.OK,
            results=[
                dbpb.PostsEntry(
                    global_id=3,
                    author_id=123,
                    title="Test",
                    body="Test body",
                    ap_id="https://rabble.cian.com/@cian/3",
                ),
            ],
        )
        self.users_response = dbpb.UsersResponse(
            result_type=dbpb.UsersResponse.OK,
            results=[
                dbpb.UsersEntry(
                    global_id=123,
                    handle="cian",
                    host="rabble.cian.com",
                    display_name="Cian",
                ),
            ],
        )

    def Posts(self, *args):
        return self.posts_response

    def Users(self, *args):
        return self.users_response


class SendLikeUndoServicerTest(unittest.TestCase):
    def setUp(self):
        self.req = upb.LikeUndoDetails(
            article_id=3,
            liker_handle="cian",
        )
        self.db = MockDB()
        self.activ_util = ActivitiesUtil(Mock(), self.db)
        self.users_util = UsersUtil(Mock(), self.db)
        self.hostname = "skinny_123"
        self.servicer = SendLikeUndoServicer(
            Mock(), self.db, self.activ_util, self.users_util, self.hostname)
        self.data = None
        self.url = None
        self.activ_util.send_activity = self.save_request
        self.activ_util._get_activitypub_actor_url = lambda host, handle: (host + '/' + handle)
        self.activ_util.build_inbox_url = lambda handle, host: (host + '/' + handle + '/inbox')

    def save_request(self, data, url):
        self.data = data
        self.url = url
        return "my_response", None

    def test_foreign_request(self):
        resp = self.servicer.SendLikeUndoActivity(self.req, None)
        self.assertEqual(resp.result_type, upb.UndoResponse.OK)
        # Check the objects are correct
        self.assertEqual(self.data["type"], "Undo")
        self.assertEqual(self.data["object"]["type"], "Like")
        self.assertEqual(self.data["object"]["object"],
                         self.db.posts_response.results[0].ap_id)
        # Check the inbox was as expected
        self.assertIn(self.db.users_response.results[0].host, self.url)
        self.assertIn(self.db.users_response.results[0].handle, self.url)

    def test_local_request(self):
        self.db.posts_response.results[0].ClearField('ap_id')
        self.db.users_response.results[0].ClearField('host')
        resp = self.servicer.SendLikeUndoActivity(self.req, None)
        self.assertEqual(resp.result_type, upb.UndoResponse.OK)
        # Check the objects are correct
        self.assertEqual(self.data["type"], "Undo")
        self.assertEqual(self.data["object"]["type"], "Like")
        self.assertIn(self.hostname, self.data["object"]["object"])
        # Check the inbox was as expected
        self.assertIn(self.hostname, self.url)
        self.assertIn(self.db.users_response.results[0].handle, self.url)

    def test_sending_error(self):
        self.activ_util.send_activity = lambda *_: (None, "Error 404")
        resp = self.servicer.SendLikeUndoActivity(self.req, None)
        self.assertEqual(resp.result_type, upb.UndoResponse.ERROR)

    def test_no_article(self):
        self.db.posts_response.ClearField('results')
        resp = self.servicer.SendLikeUndoActivity(self.req, None)
        self.assertEqual(resp.result_type, upb.UndoResponse.ERROR)

    def test_no_user(self):
        self.db.users_response.ClearField('results')
        resp = self.servicer.SendLikeUndoActivity(self.req, None)
        self.assertEqual(resp.result_type, upb.UndoResponse.ERROR)
