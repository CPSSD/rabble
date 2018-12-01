import os
import sys
from urllib.parse import urlparse

from services.proto import database_pb2
from services.proto import follows_pb2
from services.proto import rss_pb2


class RssFollowServicer:

    def __init__(self, logger, util, users_util,
                 database_stub, rss_stub):
        self._logger = logger
        self._util = util
        self._users_util = users_util
        self._database_stub = database_stub
        self._rss_stub = rss_stub

    def _convert_rss_url_to_handle(self, url):
        # Converts url in form: https://news.ycombinator.com/rss
        # to: news.ycombinator.com-rss
        if url.startswith("http"):
            url = url.split("//")[1]
        return url.replace("/", "-")

    def _validate_url(self, url):
        # TODO(sailslick) check url path? add more checks to the parsed_url
        parsed_url = urlparse(url)
        if not parsed_url.hostname or not parsed_url.path:
            return False
        return True

    def _create_rss_user(self, feed_url):
        # send to rss service to be created
        rss_entry = rss_pb2.NewRssFeed(
            rss_url = feed_url
        )
        rss_resp = self._rss_stub.NewRssFollow(rss_entry)

        # check response for new/rss service id
        if (rss_resp.result_type == rss_pb2.NewRssFeedResponse.ERROR or
            rss_resp.result_type == rss_pb2.NewRssFeedResponse.DENIED):
            self._logger.error("Rss service couldn't follow url: %s", feed_url)
            return None, rss_resp.message
        return rss_resp.global_id, None


    def RssFollowRequest(self, req, context):
        resp = follows_pb2.FollowResponse()
        self._logger.info("Got follow rss request.")

        # check if url has right endings
        valid_url = self._validate_url(req.feed_url)
        if not valid_url:
            self._logger.error("Invalid rss/atom url: %s", req.feed_url)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = "Invalid rss/atom url"
            return resp

        # check if rss user already exists (handle: domain) (local user so no host)
        rss_handle = self._convert_rss_url_to_handle(req.feed_url)
        rss_entry = self._users_util.get_user_from_db(handle=rss_handle)
        if rss_entry is None:
            # send to rss service to be created
            rss_user_id, rss_error = self._create_rss_user(req.feed_url)
            if rss_error:
                resp.result_type = follows_pb2.FollowResponse.ERROR
                resp.error = rss_error
                return resp
        else:
            rss_user_id = rss_entry.global_id

        # Get local user id
        follower_entry = self._users_util.get_user_from_db(handle=req.follower)
        if follower_entry is None:
            error = "Could not find local user {}".format(req.follower)
            self._logger.error(error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = error
            return resp

        self._logger.info("User ID %d has requested to follow User ID %d",
                          follower_entry.global_id,
                          rss_user_id)

        # Add follower
        follow_resp = self._util.create_follow_in_db(follower_entry.global_id,
                                                     rss_user_id)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error("Error creating follow: %s", follow_resp.error)
            resp.result_type = follows_pb2.FollowResponse.ERROR
            resp.error = "Could not add requested follow to database"
            return resp

        resp.result_type = follows_pb2.FollowResponse.OK
        return resp
