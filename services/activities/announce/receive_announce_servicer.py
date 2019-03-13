import os

from services.proto import database_pb2 as db_pb
from services.proto import announce_pb2
from services.proto import article_pb2
from announce_util import AnnounceUtil


class ReceiveAnnounceServicer:
    def __init__(self, logger, db, users_util, activ_util, article_stub, hostname=None):
        self._logger = logger
        self._db = db
        self._users_util = users_util
        self._activ_util = activ_util
        # Use the hostname passed in or get it manually
        self._hostname = hostname if hostname else os.environ.get('HOST_NAME')
        self._announce_util = AnnounceUtil(logger, db, activ_util, self._hostname)
        self._article_stub = article_stub
        if not self._hostname:
            self._logger.error("'HOST_NAME' env var is not set and no hostname is passed in")
            sys.exit(1)

    def get_user_by_ap_id(self, actor_tuple):
        host = self._activ_util.get_host_name_param(actor_tuple[0], self._hostname)
        if host is None:
            user = self._users_util.get_user_from_db(
                handle=actor_tuple[1], host_is_null=True)
        else:
            user = self._users_util.get_user_from_db(
                handle=actor_tuple[1], host=actor_tuple[0], host_is_null=False)
        if user is None:
            self._logger.error("User does not exist in database")
            return None
        return user

    def parse_actor_error(self, actor_name, actor_id):
        self._logger.error(
            "Received error while parsing %s author id: %s",
            actor_name,
            actor_id)
        return announce_pb2.AnnounceResponse(
            result_type=announce_pb2.AnnounceResponse.ERROR,
            error="Could not parse {} author id".format(actor_name),
        )

    def send_to_followers(self, author, announce_time, announcer_id, announced_object, response):
        parsed_ts = self._activ_util.timestamp_to_rfc(announce_time)
        activity = self._announce_util.build_announce_activity(
            announcer_id, announced_object, parsed_ts)

        # Create a list of foreign followers
        follow_list = self._users_util.get_follower_list(author.global_id)
        foreign_follows = self._users_util.remove_local_users(follow_list)

        # Send activity to all followers
        response = self._announce_util.send_announce_activity(
            foreign_follows, activity, response)
        return response

    def create_post(self, author, req):
        self._logger.debug("Calling article service with new foreign article")
        # set flag in article service that is foreign (so no need to create service)
        na = article_pb2.NewArticle(
            author=author.handle,
            author_id=author.global_id,
            title=req.title,
            body=req.body,
            creation_datetime=req.published,
            foreign=True,
            ap_id=req.announced_object,
        )
        article_resp = self._article_stub.CreateNewArticle(na)
        if article_resp.result_type == article_pb2.NewArticleResponse.ERROR:
            self._logger.error(
                "New foreign article creation returned error: %s",
                article_resp.error
            )
            return None
        article, err = self._activ_util.get_article_by_ap_id(req.announced_object)
        if err is not None:
            self._logger.error(
                "Could not find new article ap_id: % after creation: %s",
                req.announced_object,
                err
            )
            return None
        return article

    def add_share_update_count(self, announcer, article, announce_datetime):
        self._logger.debug("Adding share")
        req = db_pb.ShareEntry(
            user_id=announcer.global_id,
            article_id=article.global_id,
            announce_datetime=announce_datetime
        )
        resp = self._db.AddShare(req)
        if resp.result_type != db_pb.AddShareResponse.OK:
            self._logger.error(
                "Received error while adding share %s",
                resp.error)
            return announce_pb2.AnnounceResponse(
                result_type=announce_pb2.AnnounceResponse.ERROR,
                error="Could not add share to db {}".format(resp.error),
            )
        return None

    def ReceiveAnnounceActivity(self, req, context):
        self._logger.debug("Received announce for %s of %s from %s at %s",
                           req.target_id,
                           req.announced_object,
                           req.announcer_id,
                           req.announce_time.seconds)
        response = announce_pb2.AnnounceResponse(
            result_type=announce_pb2.AnnounceResponse.OK)

        # Parse announcer, author and target ids
        author_tuple = self._users_util.parse_actor(req.author_ap_id)
        if author_tuple[0] is None:
            return parse_actor_error("author", req.author_ap_id)
        announcer_tuple = self._users_util.parse_actor(req.announcer_id)
        if announcer_tuple[0] is None:
            return parse_actor_error("announcer", req.announcer_id)

        author = self.get_user_by_ap_id(author_tuple)
        # TODO(sailslick) check if author is actual author/post exists irl
        # https://github.com/CPSSD/rabble/issues/409
        if author is None:
            self._logger.debug("Author does not exist on this server, creating")
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
            article = self.create_post(author, req)
            if article is None:
                self._logger.debug("Issue creating new article from unknown author")
                return announce_pb2.AnnounceResponse(
                    result_type=announce_pb2.AnnounceResponse.ERROR,
                    error="Could not create local version of article id: {}".format(
                        req.announced_object),
                )
        else:
            # Check if announcer exists
            announcer = self.get_user_by_ap_id(announcer_tuple)
            if announcer is None:
                # If announcer doesn't exist, target is follower of author
                # Add announcer
                announcer = self._users_util.get_or_create_user_from_db(
                    handle=announcer_tuple[1], host=announcer_tuple[0])

            # Check if article exists
            article, err = self._activ_util.get_article_by_ap_id(req.announced_object)
            if err is not None and (author.host_is_null or not author.host):
                # Author is local but the post doesn't exist.
                # This is a bad request.
                self._logger.error(
                    "Received announce with local author for post that doesn't exist")
                return announce_pb2.AnnounceResponse(
                    result_type=announce_pb2.AnnounceResponse.ERROR,
                    error="Announce with local author for post that doesn't exist",
                )
            elif err is not None:
                message = "Could not find new article ap_id: {} even though author exists".format(
                    req.announced_object)
                self._logger.debug(message)
                # TODO(sailslick) check when author is foreign, maybe we didn't get article?
                # But this requires checking the ap_id of article and matching to author
                # Also check if author actually wrote this
                # https://github.com/CPSSD/rabble/issues/409
                # Create post
                article = self.create_post(author, req)
                if article is None:
                    return announce_pb2.AnnounceResponse(
                        result_type=announce_pb2.AnnounceResponse.ERROR,
                        error="Could not create local version of article id: {}".format(
                            req.announced_object),
                    )
            elif author.host_is_null or not author.host:
                self._logger.debug("Author and article local")
                # author and article local, check if author is target.
                # if not target, send success as author will receive share
                if req.target_id != req.author_ap_id:
                    self._logger.debug("Target is local but not author, returning success")
                    return response
                # if target, add to shares db, update share count, send to followers
                err_resp = self.add_share_update_count(announcer, article, req.announce_time)
                if err_resp is not None:
                    return err_resp
                article_obj = self._announce_util.build_article_object(
                    article, req.announced_object, req.author_ap_id)
                return self.send_to_followers(author, req.announce_time,
                                              req.announcer_id,
                                              article_obj, response)

        # At this point, author, announcer and article all exist.
        err_resp = self.add_share_update_count(announcer, article, req.announce_time)
        if err_resp is not None:
            return err_resp
        return response
