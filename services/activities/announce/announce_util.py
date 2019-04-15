from services.proto import announce_pb2


class AnnounceUtil:
    def __init__(self, logger, db, activ_util, hostname):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util
        self._hostname = hostname

    def build_announce_activity(self, actor, article_obj, published):
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Announce",
            "actor": actor,
            "object": article_obj,
            "published": published,
        }

    def build_article_object(self, article, article_url, author_actor):
        # TODO(sailslick) remove everything other than url when discover service
        # can find search for articles from a url
        timestamp = self._activ_util.timestamp_to_rfc(
            article.creation_datetime)
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

    def send_announce_activity(self, target_list, activity,
                               response, sender_id=None):
        # go through all targets and send announce activity
        # TODO (sailslick) make async/ parallel in the future
        for target in target_list:
            host = target.host
            if not host or host == "":
                host = self._hostname
            target_actor = self._activ_util.build_actor(target.handle, host)
            activity["target"] = target_actor
            inbox = self._activ_util.build_inbox_url(target.handle, host)
            resp, err = self._activ_util.send_activity(activity,
                                                       inbox,
                                                       sender_id=sender_id)
            if err is not None:
                response.result_type = announce_pb2.AnnounceResponse.ERROR
                response.error = err
        return response
