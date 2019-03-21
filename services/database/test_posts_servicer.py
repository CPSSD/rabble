import unittest
import logging
import os

import posts_servicer
import users_servicer
import like_servicer
import follow_servicer
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
        self.like = like_servicer.LikeDatabaseServicer(self.db, logger)
        self.follow = follow_servicer.FollowDatabaseServicer(self.db, logger)
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

    def add_like(self, liker_id, article_id):
        req = database_pb2.LikeEntry(
            user_id=liker_id,
            article_id=article_id,
        )
        res = self.like.AddLike(req, self.ctx)
        self.assertNotEqual(res.result_type, database_pb2.DBLikeResponse.ERROR)
        return res

    def add_follow(self, follower_id, followed_id,
                   state=database_pb2.Follow.ACTIVE):
        entry = database_pb2.Follow(
            follower=follower_id,
            followed=followed_id,
            state=state,
        )
        req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.INSERT,
            entry=entry,
        )
        res = self.follow.Follow(req, self.ctx)
        self.assertNotEqual(res.result_type,
                            database_pb2.DbFollowResponse.ERROR)
        return res

    def add_user(self, handle=None, host=None):
        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
            host_is_null=host is None,
        )

        req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.INSERT,
            entry=user_entry,
        )
        add_res = self.users.Users(req, self.ctx)
        self.assertNotEqual(add_res.result_type,
                            database_pb2.UsersResponse.ERROR)
        return add_res

    def instance_feed(self, n, user=None):
        req = database_pb2.InstanceFeedRequest(num_posts=n)
        if user is not None:
            req.user_global_id.value = user
        res = self.posts.InstanceFeed(req, self.ctx)
        self.assertNotEqual(res.result_type, database_pb2.PostsResponse.ERROR)
        return res

    def find_post(self, user, author_id=None):
        req = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.FIND
        )
        if author_id is not None:
            req.match.author_id = author_id
        req.user_global_id.value = user
        res = self.posts.Posts(req, self.ctx)
        self.assertNotEqual(res.result_type, database_pb2.PostsResponse.ERROR)
        return res


class PostsDatabase(PostsDatabaseHelper):

    def test_no_foreign_posts_in_instance_feed(self):
        self.add_user(handle='tayne', host=None)  # local user, id 1
        self.add_user(handle='nude_tayne', host='celery.com')  # foreign, id 2
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

    def test_limit_works_in_instance_feed(self):
        self.add_user(handle='tayne', host=None)  # local user, id 1
        self.add_post(author_id=1, title='1 kissie', body='for the boys')
        self.add_post(author_id=1, title='2 kissies', body='for the boys')
        self.add_post(author_id=1, title='3 kissies', body='for the boys')

        res = self.instance_feed(2)
        want0 = database_pb2.PostsEntry(
            global_id=2,
            author_id=1,
            title='2 kissies',
            body='for the boys',
            creation_datetime={},
        )
        want1 = database_pb2.PostsEntry(
            global_id=3,
            author_id=1,
            title='3 kissies',
            body='for the boys',
            creation_datetime={},
        )
        self.assertEqual(len(res.results), 2)
        self.assertIn(want0, res.results)
        self.assertIn(want1, res.results)

    def test_instance_feed_is_liked(self):
        self.add_user(handle='tayne', host=None)
        self.add_user(handle='paul', host=None)
        self.add_post(author_id=1, title='1 kissie', body='for the boys')
        self.add_like(liker_id=2, article_id=1)
        self.add_post(author_id=1, title='2 kissies', body='for the boys')

        res = self.instance_feed(n=2, user=2)
        want0 = database_pb2.PostsEntry(
            global_id=1,
            author_id=1,
            title='1 kissie',
            body='for the boys',
            creation_datetime={},
            likes_count=1,
            is_liked=True,
        )
        want1 = database_pb2.PostsEntry(
            global_id=2,
            author_id=1,
            title='2 kissies',
            body='for the boys',
            creation_datetime={},
            is_liked=False,
        )
        self.assertEqual(len(res.results), 2)
        self.assertIn(want0, res.results)
        self.assertIn(want1, res.results)

    def test_posts_is_liked(self):
        self.add_user(handle='tayne', host=None)
        self.add_user(handle='paul', host=None)
        self.add_post(author_id=1, title='1 kissie', body='for the boys')
        self.add_like(liker_id=2, article_id=1)
        self.add_post(author_id=1, title='2 kissies', body='for the boys')
        self.add_post(author_id=2, title='72 kissies', body='for the noah')

        res = self.find_post(user=2, author_id=1)
        want0 = database_pb2.PostsEntry(
            global_id=1,
            author_id=1,
            title='1 kissie',
            body='for the boys',
            creation_datetime={},
            likes_count=1,
            is_liked=True,
        )
        want1 = database_pb2.PostsEntry(
            global_id=2,
            author_id=1,
            title='2 kissies',
            body='for the boys',
            creation_datetime={},
            is_liked=False,
        )
        self.assertEqual(len(res.results), 2)
        self.assertIn(want0, res.results)
        self.assertIn(want1, res.results)

    def test_instance_feed_is_followed(self):
        self.add_user(handle='tayne', host=None)
        self.add_user(handle='paul', host=None)
        self.add_user(handle='rudd', host=None)
        self.add_post(author_id=1, title='1 kissie', body='for the boys')
        self.add_follow(follower_id=2, followed_id=1)
        self.add_post(author_id=1, title='2 kissies', body='for the boys')
        self.add_post(author_id=3, title='3 kissies', body='for the boys')

        res = self.instance_feed(n=3, user=2)
        want0 = database_pb2.PostsEntry(
            global_id=1,
            author_id=1,
            title='1 kissie',
            body='for the boys',
            creation_datetime={},
            is_followed=True,
        )
        want1 = database_pb2.PostsEntry(
            global_id=2,
            author_id=1,
            title='2 kissies',
            body='for the boys',
            creation_datetime={},
            is_followed=True,
        )
        want2 = database_pb2.PostsEntry(
            global_id=3,
            author_id=3,
            title='3 kissies',
            body='for the boys',
            creation_datetime={},
            is_followed=False,
        )
        self.assertEqual(len(res.results), 3)
        self.assertIn(want0, res.results)
        self.assertIn(want1, res.results)
        self.assertIn(want2, res.results)

    def test_posts_is_followed(self):
        self.add_user(handle='tayne', host=None)
        self.add_user(handle='paul', host=None)
        self.add_post(author_id=1, title='1 kissie', body='for the boys')
        self.add_follow(follower_id=2, followed_id=1)
        self.add_post(author_id=1, title='2 kissies', body='for the boys')
        self.add_post(author_id=2, title='72 kissies', body='for the noah')

        res = self.find_post(user=2, author_id=1)
        want0 = database_pb2.PostsEntry(
            global_id=1,
            author_id=1,
            title='1 kissie',
            body='for the boys',
            creation_datetime={},
            is_followed=True,
        )
        want1 = database_pb2.PostsEntry(
            global_id=2,
            author_id=1,
            title='2 kissies',
            body='for the boys',
            creation_datetime={},
            is_followed=True,
        )
        self.assertEqual(len(res.results), 2)
        self.assertIn(want0, res.results)
        self.assertIn(want1, res.results)

    def test_posts_no_filter(self):
        self.add_user(handle='tayne', host=None)  # local user, id 1
        self.add_user(handle='tayne2', host=None)  # local user, id 2
        self.add_post(author_id=1, title='1 kissie', body='for the boys')
        self.add_post(author_id=1, title='2 kissies', body='for the boys')

        res = self.find_post(user=2)
        want0 = database_pb2.PostsEntry(
            global_id=1,
            author_id=1,
            title='1 kissie',
            body='for the boys',
            creation_datetime={},
        )
        want1 = database_pb2.PostsEntry(
            global_id=2,
            author_id=1,
            title='2 kissies',
            body='for the boys',
            creation_datetime={},
        )
        self.assertEqual(len(res.results), 2)
        self.assertIn(want0, res.results)
        self.assertIn(want1, res.results)
