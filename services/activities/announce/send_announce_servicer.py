import os
import sys
import json
from urllib import request

from services.proto import database_pb2
from services.proto import announce_pb2


class SendAnnounceServicer:
    def __init__(self, logger, db, users_util, activ_util, hostname=None):
        self._logger = logger
        self._db = db
        self._users_util = users_util
        self._activ_util = activ_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get("HOST_NAME")
        if not self._hostname:
            self._logger.error("'HOST_NAME' env var is not set")
            sys.exit(1)

    def _build_article_object(self, article_url):
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Article",
            "url": article_url,
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

        # Get post originator
        article, err = self._get_shared_article(req.article_id)
        if err != None:
            response.result_type = announce_pb2.AnnounceResponse.ERROR
            response.error = "Shared Article does not exist"
            return response

        originator = self._users_util.get_user_from_db(global_id=article.author_id)
        if announcer is None:
            response.result_type = announce_pb2.AnnounceResponse.ERROR
            response.error = "Author of shared post does not exist"
            return response

        # Create Announce activity
        article_url = ""  # self._activ_util.build_article_id(originator, article)
        creation_datetime = req.annnounce_time.ToJsonString()
        actor = self._activ_util.build_actor(announcer.handle, self._host_name)
        article_obj = self._build_article_object(article_url)
        announce_activity = self._build_announce_activity(
            actor, article_obj, creation_datetime)

        # Create a list of foreign followers
        follow_list = self._users_util.get_follower_list(req.announcer_id)
        foreign_follows = self._users_util.remove_local_users(follow_list)

        # Add article originator if not in list
        # This is so they can increment their share count
        if originator not in foreign_follows:
            foreign_follows.append(originator)

        # go through all follows and send announce activity
        # TODO (sailslick) make async/ parallel in the future
        for follower in foreign_follows:
            target = self._activ_util.build_actor(follower.handle, follower.host)
            announce_activity["target"] = target
            inbox = self._activ_util.build_inbox_url(follower.handle, follower.host)
            resp, err = self._activ_util.send_activity(announce_activity, inbox)
            if err is not None:
                response.result_type = announce_pb2.AnnounceResponse.ERROR
                response.error = err

        return response
