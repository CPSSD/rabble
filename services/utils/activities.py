import json
from urllib import request


class ActivitiesUtil:
    def __init__(self, logger):
        self._logger = logger

    def build_actor(self, handle, host):
        s = f'{host}/ap/@{handle}'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def build_article(self, author, article):
        """
        author must be a UserEntry proto.
        article must be a PostEntry proto.
        """
        if article.ap_id:
            return article.ap_id
        # Local article, build ID manually
        s = f'{author.host}/@{author.handle}/{article.global_id}'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def build_delete(self, obj):
        return {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Delete",
            "object": obj
        }

    def build_inbox_url(self, handle, host):
        # TODO(CianLR): Remove dupe logic from here and UsersUtil.
        s = f'{host}/ap/@{handle}/inbox'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def send_activity(self, activity, target_inbox):
        body = json.dumps(activity).encode("utf-8")
        headers = {"Content-Type": "application/ld+json"}
        req = request.Request(target_inbox,
                              data=body,
                              headers=headers,
                              method='POST')
        self._logger.debug('Sending activity to foreign server: %s',
                           target_inbox)
        try:
            resp = request.urlopen(req)
        except Exception as e:
            self._logger.error('Error trying to send activity:' + str(e))
            return None, str(e)
        return resp, None
