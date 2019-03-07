import os

from services.proto import database_pb2 as db_pb
from services.proto import announce_pb2
from announce_util import AnnounceUtil


class ReceiveAnnounceServicer:
    def __init__(self, logger, db, users_util, activ_util, hostname=None):
        self._logger = logger
        self._db = db
        self._users_util = users_util
        self._activ_util = activ_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get('HOST_NAME')
        self._announce_util = AnnounceUtil(logger, _db, activ_util)
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

    def parse_actor_error(actor_name, actor_id):
        self._logger.error(
            "Received error while parsing %s author id: %s",
            actor_name,
            actor_id)
        return announce_pb2.AnnounceResponse(
            result_type=announce_pb2.AnnounceResponse.ERROR,
            error="Could not parse {} author id".format(actor_name),
        )

    def add_to_shares_db():
        pass

    def update_share_count():
        pass

    def send_to_followers():
        pass

    def create_post():
        pass

    def ReceiveAnnounceActivity(self, req, context):
        self._logger.debug("Got announce for %s from %s at %s",
                           req.announced_object,
                           req.announcer_id,
                           req.announce_time)
        response = announce_pb2.AnnounceResponse(
            result_type=announce_pb2.AnnounceResponse.OK)

        # Parse announcer, author and target ids
        author_tuple = self._users_util.parse_actor(req.author_ap_id)
        if author_tuple[0] is None:
            return parse_actor_error("author", req.author_ap_id)
        announcer_tuple = self._users_util.parse_actor(req.announcer_id)
        if announcer_tuple[0] is None:
            return parse_actor_error("announcer", req.announcer_id)
        target_tuple = self._users_util.parse_actor(req.announcer_id)
        if announcer_tuple[0] is None:
            return parse_actor_error("target", req.target_id)

        author = self.get_user_by_ap_id(author_tuple)
        # TODO(sailslick) check if author is actual author/post exists irl
        # https://github.com/CPSSD/rabble/issues/409
        if author is None:
            # Author is foreign and doesn't exist.
            # Check if announcer exists
            announcer = self.get_user_by_ap_id(announcer_tuple)
            if announcer is None:
                # If announcer & author doesn't exist, announce is error
                self._logger.error("Received announce without knowing author or announcer")
                return announce_pb2.AnnounceResponse(
                    result_type=announce_pb2.AnnounceResponse.ERROR,
                    error="Received announce without knowing author or announcer",
                )

            # Follower of announcer
            # Create author.
            author = self._users_util.get_or_create_user_from_db(
                handle=author_tuple[1], host=author_tuple[0])
            # Create post
            article = self.create_post()
            ok = self.add_to_shares_db()
            if not ok:
                self.update_share_count()
        else:
            article, err = self._activ_util.get_article_by_ap_id(req.announced_object)
            if err is not None:
                # TODO(sailslick) check when author is foreign, maybe we didn't get article?
                # But this requires checking the ap_id of article and matching to author
                # Also check if author actually wrote this
                # https://github.com/CPSSD/rabble/issues/409
                # Create post
                article = self.create_post()
                ok = self.add_to_shares_db()
                if not ok:
                    self.update_share_count()
            if author.host_is_null or not author.host:
                # author and article local, check if author is target.
                # if not target, send success as author will receive share
                if req.target_id != req.author_id:
                    return response
                # if target, add to shares db, update share count, send to followers
                ok = self.add_to_shares_db()
                if not ok:
                    self.update_share_count()
                self.send_to_followers()
                return response

            # author in db but not local
            announcer = self.get_user_by_ap_id(announcer_tuple)
            if announcer is None:
                # If announcer doesn't exist, is follower of author, just increment
                self.update_share_count()
                return response

            # If announcer exists, sent to announcer follower or to announcer
            ok = self.add_to_shares_db()
            if not ok:
                self.update_share_count()

        return response
