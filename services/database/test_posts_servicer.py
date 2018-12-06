import unittest
import logging
import os
from functools import partial

import posts_servicer
import users_servicer
import database
from services.proto import database_pb2

POSTS_DB_PATH = "./testdb/posts.db"

class PostsDatabaseHelper(unittest.TestCase):
    def setUp(self):
        def clean_database():
            os.remove(POSTS_DB_PATH)

        def fake_context():
            def called():
                raise NotImplemented
            return called

        logger = logging.getLogger()
        self.db = database.build_database(logger,
                                          "rabble_schema.sql",
                                          POSTS_DB_PATH)
        self.addCleanup(clean_database)
        self.posts = posts_servicer.PostsDatabaseServicer(self.db, logger)
        self.users = users_servicer.UsersDatabaseServicer(self.db, logger)
        self.ctx = fake_context()

    def add_post(self, author_id=None, title=None, body=None):
        post_entry = database_pb2.PostsEntry(
            author_id=author_id,
            title=title,
            body=body,
        )

        req = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.INSERT,
            entry=post_entry,
        )

        add_res = self.posts.Posts(req, self.ctx)
        self.assertNotEqual(add_res.result_type,
                            database_pb2.PostsResponse.ERROR)
        return add_res

    def add_user(self, handle=None, host=None):
        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
        )

        req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.INSERT,
            entry=user_entry,
        )
        add_res = self.users.Users(req, self.ctx)
        self.assertNotEqual(add_res.result_type,
                            database_pb2.UsersResponse.ERROR)
        return add_res

    def instance_feed(self, n):
        req = database_pb2.InstanceFeedRequest(num_posts=n)
        res = self.posts.InstanceFeed(req, self.ctx)
        self.assertNotEqual(res.result_type, database_pb2.PostsResponse.ERROR)
        return res

class PostsDatabase(PostsDatabaseHelper):
    def test_no_foreign_posts_in_instance_feed(self):
        self.add_user(handle='tayne', host=None) # local user, id 1
        self.add_user(handle='nude_tayne', host='celery.com') # foreign, id 2
        self.add_post(author_id=1, title='hi', body='hello sam')
        self.add_post(author_id=2, title='yo', body='sammy!')

        res = self.instance_feed(3)
        want = database_pb2.PostsEntry(
            global_id=1,
            author_id=1,
            title='hi',
            body='hello sam',
            creation_datetime={},
        )
        self.assertEqual(len(res.results), 1)
        self.assertIn(want, res.results)
