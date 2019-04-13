import json
import sys
import time
import os

from services.proto import database_pb2

import requests

from requests_http_signature import HTTPSignatureHeaderAuth


class ActivitiesUtil:
    def __init__(self, logger, db):
        host_name = os.environ.get("HOST_NAME")
        if not host_name:
            print("Please set HOST_NAME env variable")
        self._host_name = host_name
        self._logger = logger
        self._db = db

    @staticmethod
    def rabble_context():
        return "https://www.w3.org/ns/activitystreams"

    def _get_webfinger_document(self, normalised_host, handle):
        """
        Fetch the webfinger document for the user with the given handle on the
        given host.
        """
        self._logger.debug(
            'Fetching webfinger doc for user {}@{}'.format(handle,
                                                           normalised_host))
        # Webfinger users are of the form `bob@example.com`, so remove the
        # protocol from the host if it's there.
        host_no_protocol = self._remove_protocol_from_host(normalised_host)
        username = '{}@{}'.format(handle, host_no_protocol)
        url = f'{normalised_host}/.well-known/webfinger?resource=acct:{username}'
        resp = requests.get(url)
        if resp.status_code < 200 or resp.status_code >= 300:
            self._logger.warning(('Non-2xx response code ({}) for webfinger '
                                  + 'lookup for URL: {}').format(resp.status_code,
                                                               url))
            return None
        return resp.json()

    def _parse_actor_url_from_webfinger(self, doc):
        """
        Given a webfinger document, parse out the actor's URL and return it.
        """
        if 'links' not in doc:
            self._logger.warning('No "links" field in webfinger document.')
            return None
        for link in doc['links']:
            if link['rel'] == 'self':
                return link['href']
        self._logger.warning('No link with "rel" field = "self" found in '
                             'webfinger document.')
        return None

    def _get_activitypub_actor_url(self, normalised_host, handle):
        """
        Fetch the webfinger document for a given user, and return the actor ID
        URL from it.
        """
        if normalised_host is None or normalised_host == self.normalise_hostname(self._host_name):
            return self._build_local_actor_url(handle, normalised_host)
        webfinger_doc = self._get_webfinger_document(normalised_host, handle)
        if webfinger_doc is None:
            return None
        return self._parse_actor_url_from_webfinger(webfinger_doc)

    def normalise_hostname(self, hostname):
        if hostname is None:
            return hostname
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

    def _remove_protocol_from_host(self, host):
        return host.split('://')[-1]

    def _build_local_actor_url(self, handle, normalised_host):
        return f'{normalised_host}/ap/@{handle}'

    def _get_user_by_id(self, _id):
        """
        Get the user object for the given user global_id. If the user could not
        be retrieved, return None.
        """
        user_resp = self._db.Users(database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            match=database_pb2.UsersEntry(global_id=_id)))
        if user_resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.warning(
                'Could not find user: {}'.format(user_resp.error))
            return None
        if not len(user_resp.results):
            self._logger.warning('Could not find user.')
            return None
        return user_resp.results[0]

    def _get_private_key(self, user_obj):
        """
        Return the private key byte array from the given user object.
        """
        return user_obj.private_key.encode('utf-8')

    def _get_key_id(self, user_obj):
        """
        Return the Key ID for the HTTP Signature from the given user object.
        """
        handle = user_obj.handle
        normalised_host = self.normalise_hostname(self._host_name)
        return '{}#main-key'.format(self._build_local_actor_url(handle,
                                                                normalised_host))

    def build_actor(self, handle, host):
        """
        Return the actor ID/URL for the user with the given handle and host.
        Firstly, normalise & add protocol to the given host.
        - If the given user is local, then build the string with the host and
          handle.
        - If the given user is foreign, then fetch their Webfinger document and
          extract the actor URL from it.
        To use this function, the `HOST_NAME` env var should be set.
        """
        normalised_host = self.normalise_hostname(host)
        if host == self._host_name or host is None:
            self._logger.info('Building actor for local user')
            return self._build_local_actor_url(handle, normalised_host)
        actor_url = self._get_activitypub_actor_url(normalised_host, handle)
        return actor_url

    def get_host_name_param(self, host, hostname):
        # Remove protocol
        foreign_host = host.split('://')[-1]
        local_host = hostname.split('://')[-1]
        if foreign_host == local_host:
            return None
        return host

    def build_article_ap_id(self, author, article):
        """
        author must be a UserEntry proto.
        article must be a PostEntry proto.
        """
        if article.ap_id:
            return article.ap_id
        # Local article, build ID manually
        normalised_host = self.normalise_hostname(author.host)
        if normalised_host is None or author.host == "":
            normalised_host = self.normalise_hostname(self._host_name)
        return f'{normalised_host}/ap/@{author.handle}/{article.global_id}'

    def build_local_article_url(self, author, article):
        """
        author must be a UserEntry proto.
        article must be a PostEntry proto.
        """
        # Local article, build ID manually
        normalised_host = self.normalise_hostname(self._host_name)
        return f'{normalised_host}/#/@{author.handle}/{article.global_id}'

    def build_undo(self, obj):
        return {
            "@context": self.rabble_context(),
            "type": "Undo",
            "object": obj
        }

    def build_delete(self, user, article, hostname):
        """
        Build a delete activity.
        user is a UsersEntry proto.
        article is a PostsEntry proto.
        """
        return {
            "@context": self.rabble_context(),
            "type": "Delete",
            "object": self.build_article_ap_id(user, article),
            "actor": self.build_actor(user.handle, hostname),
        }

    def fetch_actor(self, actor_url):
        """
        Fetch the actor document at the given URL, and return the parsed JSON
        as a dict.
        """
        # Mastodon requires the Accept header to be set, otherwise it redirects
        # to the user-facing page for this user.
        headers = {
            'Accept': 'application/activity+json, application/ld+json'
        }

        # Fetch the actor document.
        resp = requests.get(actor_url, headers=headers)
        if resp.status_code < 200 or resp.status_code >= 300:
            self._logger.warning(('Non-2xx response ({}) when fetching actor '
                                  + 'document at URL "{}"').format(resp.status_code,
                                                                 actor_url))
            return None
        doc = resp.json()
        return doc

    def build_inbox_url(self, handle, host):
        """
        Fetch the inbox URL for the user with the given handle and host.
        If there is any error, return None.
        """
        normalised_host = self.normalise_hostname(host)

        # Get the URL of this user's actor document.
        actor_url = self._get_activitypub_actor_url(normalised_host, handle)
        if actor_url is None:
            self._logger.warning('Actor URL is None.')
            return None
        if host is None or host == self._host_name:
            return '{}/inbox'.format(actor_url)

        doc = self.fetch_actor(actor_url)
        if doc is None:
            self._logger.warning(
                f'No actor document received for url {actor_url}')
            return None
        inbox_url = doc['inbox']
        self._logger.info('Found inbox URL {} for user {} at host {}'.format(
            inbox_url, handle, host))
        return inbox_url

    def build_article(self, ap_id, title, timestamp, author, content, summary, article_url=None):
        """
        Builds an ActivityPub article object.
        The timestamp must be in json format, not protobuf.
        """
        if article_url is None:
            article_url = ap_id
        return {
            "@context": self.rabble_context(),
            "type": "Article",
            "id": ap_id,
            "name": title,
            "published": timestamp,
            "attributedTo": author,
            "content": content,
            "preview": {
                "type": "Note",
                "name": "Summary",
                "content": summary,
            },
            "url": article_url,
        }

    def send_activity(self, activity, target_inbox, sender_id=None):
        body = json.dumps(activity).encode("utf-8")
        headers = {"Content-Type": "application/ld+json"}

        auth = None
        if sender_id is not None:
            user_obj = self._get_user_by_id(sender_id)
            private_key = self._get_private_key(user_obj)
            key_id = self._get_key_id(user_obj)
            headers['keyId'] = key_id
            auth = HTTPSignatureHeaderAuth(algorithm="rsa-sha256",
                                           key=private_key,
                                           key_id=key_id)
            self._logger.info('Signing activity with key_id {}'.format(key_id))

        req = requests.Request('POST', target_inbox,
                               data=body, headers=headers, auth=auth)
        req = req.prepare()
        self._logger.debug('Sending activity to foreign server (%s):\n%s',
                           target_inbox, body)
        try:
            resp = requests.Session().send(req)
            self._logger.info('Got response: "{}" (status code {})'.format(
                resp.text, resp.status_code))
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
        return time.strftime("%Y-%m-%dT%H:%M:%S.000Z",
                             time.gmtime(timestamp.seconds))
