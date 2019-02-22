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
