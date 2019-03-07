import os
import sys
import json
from urllib import request

from services.proto import database_pb2
from services.proto import announce_pb2
from announce_util import AnnounceUtil


class SendAnnounceServicer:
    def __init__(self, logger, db, users_util, activ_util, hostname=None):
        self._logger = logger
        self._db = db
        self._users_util = users_util
        self._activ_util = activ_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get("HOST_NAME")
        self._announce_util = AnnounceUtil(logger, db, activ_util)
        if not self._hostname:
            self._logger.error("'HOST_NAME' env var is not set")
            sys.exit(1)

    def _build_article_object(self, article, article_url, author_actor):
        # TODO(sailslick) remove everything other than url when discover service
        # can find search for articles from a url
        timestamp = article.creation_datetime.ToJsonString()
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Article",
            "url": article_url,
            "name": article.title,
            "published": timestamp,
            "attributedTo": author_actor,
            "content": article.md_body,
            "id": article_url,
        }

    def _build_announce_activity(self, actor, article_obj, published):
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Announce",
            "actor": actor,
            "object": article_obj,
            "published": published,
        }

    def _get_shared_article(self, article_id):
        posts_req = db_pb.PostsRequest(
            request_type=db_pb.PostsRequest.FIND,
            match=db_pb.PostsEntry(
                global_id=article_id,
            ),
        )
        resp = self._db.Posts(posts_req)
        if resp.result_type != db_pb.PostsResponse.OK:
            return None, resp.error
        elif len(resp.results) > 1:
            return None, "Recieved too many results from DB"
        elif len(resp.results) == 0:
            return None, "No matching DB entry for this article"
        return resp.results[0], None

    def SendAnnounceActivity(self, req, context):
        self._logger.debug("Sending announce for article_id %s from %s at %s",
                           req.article_id,
                           req.announcer_id,
                           req.announce_time)
        response = announce_pb2.AnnounceResponse(
            result_type=announce_pb2.AnnounceResponse.OK)

        announcer = self._users_util.get_user_from_db(global_id=req.announcer_id)
        if announcer is None:
            response.result_type = announce_pb2.AnnounceResponse.ERROR
            response.error = "Announcer does not exist"
            return response

        # Get post author & reblogged article
        article, err = self._get_shared_article(req.article_id)
        if err != None:
            response.result_type = announce_pb2.AnnounceResponse.ERROR
            response.error = "Shared Article does not exist"
            return response

        author = self._users_util.get_user_from_db(global_id=article.author_id)
        if author is None:
            response.result_type = announce_pb2.AnnounceResponse.ERROR
            response.error = "Author of shared post does not exist"
            return response
        host = author.host
        # check if author is local
        if not author.host:
            host = self._host_name
        author_actor = self._activ_util.build_actor(author.handle, host)

        # Create Announce activity
        article_url = self._activ_util.build_article_url(author, article)
        article_obj = self._build_article_object(article, article_url, author_actor)
        actor = self._activ_util.build_actor(announcer.handle, self._host_name)
        creation_datetime = req.annnounce_time.ToJsonString()

        announce_activity = self._announce_util.build_announce_activity(
            actor, article_obj, creation_datetime)

        # Create a list of foreign followers
        follow_list = self._users_util.get_follower_list(req.announcer_id)
        foreign_follows = self._users_util.remove_local_users(follow_list)

        # Add article author if not in list
        # This is so they can increment their share count & supply to followers
        if author not in foreign_follows:
            foreign_follows.append(author)

        # Add announcer so local instance can add to share db
        if announcer not in foreign_follows:
            foreign_follows.append(announcer)

        # Send activity to all followers
        response = self._announce_util.send_announce_activity(
            foreign_follows, announce_activity, response)

        return response
