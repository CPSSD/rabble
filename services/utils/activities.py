import json
import time
from services.proto import database_pb2

import requests


class ActivitiesUtil:
    def __init__(self, logger, db):
        self._logger = logger
        self._db = db

    @staticmethod
    def rabble_context():
        return "https://www.w3.org/ns/activitystreams"

    def get_webfinger_document(self, host, handle):
        full_username = '@{}@{}'.format(host, handle)
        url = '{}/.well_known/webfinger?resouce=acct:{}'.format(host,
                                                                full_username)
        resp = requests.get(url)
        if resp.status_code != 200:
            self._logger.warning('Non-200 response code for webfinger lookup '
                'at url: {}'.format(url))
            return None
        return resp.json()

    def parse_actor_url_from_webfinger(self, doc):
        if 'links' not in doc:
            self._logger.warning('No "links" field in webfinger document.')
            return None
        for link in doc['links']:
            if link['rel'] == 'self':
                return link['href']
        self._logger.warning('No link with "rel" field = "self" found in '
            'webfinger document.')
        return None

    def get_activitypub_actor_url(self, host, handle):
        webfinger_doc = self.get_webfinger_doc(host, handle)
        if webfinger_doc is None:
            return None
        return self.parse_actor_url_from_webfinger(webfinger_doc)


    def _normalise_hostname(self, hostname):
        if not hostname.startswith('http'):
            old_hostname = hostname
            if hostname != None and "." not in hostname:
                hostname = 'http://' + hostname
            else:
                hostname = 'https://' + hostname
            self._logger.info('Normalising hostname from "%s" to "%s".',
                              old_hostname,
                              hostname)
        return hostname

    def build_actor(self, handle, host):
        normalised_host = self._normalise_hostname(host)
        return f'{normalised_host}/ap/@{handle}'

    def get_host_name_param(self, host, hostname):
        # Remove protocol
        foreign_host = host.split('://')[-1]
        local_host = hostname.split('://')[-1]
        if foreign_host == local_host:
            return None
        return host

    def build_article_url(self, author, article):
        """
        author must be a UserEntry proto.
        article must be a PostEntry proto.
        """
        if article.ap_id:
            return article.ap_id
        # Local article, build ID manually
        normalised_host = self._normalise_hostname(author.host)
        return f'{normalised_host}/ap/@{author.handle}/{article.global_id}'

    def build_undo(self, obj):
        return {
            "@context": self.rabble_context(),
            "type": "Undo",
            "object": obj
        }

    def build_inbox_url(self, handle, host):
        # TODO(CianLR): Remove dupe logic from here and UsersUtil.
        normalised_host = self._normalise_hostname(host)
        return f'{normalised_host}/ap/@{handle}/inbox'

    def send_activity(self, activity, target_inbox):
        body = json.dumps(activity).encode("utf-8")
        headers = {"Content-Type": "application/ld+json"}
        req = requests.Request('POST', target_inbox, data=body, headers=headers)
        req = req.prepare()
        self._logger.debug('Sending activity to foreign server (%s):\n%s',
                           target_inbox, body)
        try:
            resp = requests.Session().send(req)
        except Exception as e:
            self._logger.error('Error trying to send activity:' + str(e))
            return None, str(e)
        return resp, None

    def get_article_by_ap_id(self, obj_id):
        posts_req = database_pb2.PostsRequest(
            request_type=database_pb2.PostsRequest.FIND,
            match=database_pb2.PostsEntry(
                ap_id=obj_id,
            ),
        )
        resp = self._db.Posts(posts_req)
        if resp.result_type != database_pb2.PostsResponse.OK:
            return None, resp.error
        elif len(resp.results) > 1:
            return None, "Recieved too many results from DB"
        elif len(resp.results) == 0:
            # NOTE: This can happen natually.
            # cian@a.com follows ross@b.org.
            # b.org sends a Like for an article by ross that already existed.
            # a.com didn't get the original Create so it can't find it.
            return None, "No matching DB entry for this article"
        return resp.results[0], None

    def forward_activity_to_followers(self, user_id, activity):
        """
        Sends an activity to all of the hosts with a follower of a given user.
        Some things to note about the behaviour:
         - Local users do not receive the activity
         - An arbitrary user from each host is selected to receive the activity
         - Any followers or hosts not found are skipped with a warning.
        """
        self._logger.info("Sending activity to followers")
        resp = self._db.Follow(database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=database_pb2.Follow(followed=user_id),
        ))
        if resp.result_type != database_pb2.DbFollowResponse.OK:
            return resp.error
        self._logger.info("Have %d users to notify", len(resp.results))
        # Gather up the users, filter local and non-unique hosts.
        hosts_to_users = {}
        for follow in resp.results:
            user_resp = self._db.Users(database_pb2.UsersRequest(
                request_type=database_pb2.UsersRequest.FIND,
                match=database_pb2.UsersEntry(global_id=follow.follower)))
            if user_resp.result_type != database_pb2.UsersResponse.OK:
                self._logger.warning(
                    "Error finding user %d, skipping", follow.follower)
                continue
            if len(user_resp.results) != 1:
                self._logger.warning(
                    "Couldn't find user %d, skipping", follow.follower)
                continue
            user = user_resp.results[0]
            if not user.host or user.host_is_null:
                continue  # Local user, skip.
            hosts_to_users[user.host] = user
        # Send the activities off.
        for host, user in hosts_to_users.items():
            inbox = self.build_inbox_url(user.handle, host)
            resp, err = self.send_activity(activity, inbox)
            if err:
                self._logger.warning(
                    "Error sending activity to '%s' at '%s': %s",
                    user.handle, host, str(err)
                )
        return None

    def timestamp_to_rfc(self, timestamp):
        # 2006-01-02T15:04:05.000Z
        return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp.seconds))
