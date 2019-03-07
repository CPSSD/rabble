

class AnnounceUtil:
    def __init__(self, logger, db, activ_util):
        self._logger = logger
        self._db = db
        self._activ_util = activ_util

    def build_announce_activity(self, actor, article_obj, published):
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Announce",
            "actor": actor,
            "object": article_obj,
            "published": published,
        }

    def send_announce_activity(target_list, activity, response):
        # go through all targets and send announce activity
        # TODO (sailslick) make async/ parallel in the future
        for target in target_list:
            target_actor = self._activ_util.build_actor(target.handle, target.host)
            activity["target"] = target_actor
            inbox = self._activ_util.build_inbox_url(target.handle, target.host)
            resp, err = self._activ_util.send_activity(activity, inbox)
            if err is not None:
                response.result_type = announce_pb2.AnnounceResponse.ERROR
                response.error = err
        return response
