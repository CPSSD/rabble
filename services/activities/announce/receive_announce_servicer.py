import os

from services.proto import database_pb2 as db_pb
from services.proto import announce_pb2


class ReceiveAnnounceServicer:
    def __init__(self, logger, db, users_util, activ_util, hostname=None):
        self._logger = logger
        self._db = db
        self._users_util = users_util
        self._activ_util = activ_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get('HOST_NAME')
        if not self._hostname:
            self._logger.error("'HOST_NAME' env var is not set and no hostname is passed in")
            sys.exit(1)

    def get_user_by_ap_id(self, actor_tuple):
        if actor_tuple[0] == self._hostname:
            user = self._users_util.get_user_from_db(
                handle=actor_tuple[1], host_is_null=True)
        else:
            user = self._users_util.get_user_from_db(
                handle=actor_tuple[1], host=actor_tuple[0], host_is_null=False)
        if user is None:
            self._logger.error("User does not exist in database")
            return None
        return user

    def ReceiveAnnounceActivity(self, req, context):
        self._logger.debug("Got announce for %s from %s at %s",
                           req.announced_object,
                           req.announcer_id,
                           req.announce_time)
        response = announce_pb2.AnnounceResponse(
            result_type=announce_pb2.AnnounceResponse.OK)

        # If article & author is local
        # update follow count
        # send update to all followers
        author_tuple = self._users_util.parse_actor(req.author_ap_id)
        if author_tuple[0] is None:
            self._logger.error("Received error while parsing announced author id")
            return announce_pb2.AnnounceResponse(
                result_type=announce_pb2.AnnounceResponse.ERROR,
                error="Could not get parse announced author id",
            )
        author = self.get_user_by_ap_id(author_tuple)
        if author is None:
            # author is foreign and doesn't exist. Create author.
            author = self._users_util.get_or_create_user_from_db(
                handle=author_tuple[1], host=author_tuple[0])
            # post does not exist (as author doesn't) create post
            # TODO(sailslick) check if author is actual author/post exists irl
            # https://github.com/CPSSD/rabble/issues/409
        else:
            article, err = self._activ_util.get_article_by_ap_id(req.announced_object)
            if err is not None:
                # TODO(sailslick) check when author is foreign, maybe we didn't get article?
                # But this requires checking the ap_id of article and matching to author
                # For now discard
                # https://github.com/CPSSD/rabble/issues/409
                self._logger.error("Received error while getting announced article")
                return announce_pb2.AnnounceResponse(
                    result_type=announce_pb2.AnnounceResponse.ERROR,
                    error="Could not get announced article",
                )
            else:
                # update follow count and send update
                # Add follower
                pass

            # If announcer is local
            # Add to share db
            host, handle = self._users_util.parse_actor(announcer_id)
            # Sets the host to None if the user is local.
            # TODO(CianLR): This may possibly match a user with the same
            # handle but on a different instance.

            # If article is foreign
            # add to share db
            # TODO (sailslick) get foreign article
            # TODO (sailslick) get foreign article author

        return response
