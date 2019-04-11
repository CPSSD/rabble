from urllib.parse import urlparse

import requests

from services.proto import database_pb2

from utils.activities import ActivitiesUtil

MAX_FIND_RETRIES = 3


class UsersUtil:

    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db = db_stub
        self._activ_util = ActivitiesUtil(logger, db_stub)

    def parse_username(self, username):
        username = username.lstrip('@')
        p = username.split('@')
        if len(p) == 1:
            # Local user like 'admin'.
            return p[0], None
        if len(p) == 2:
            # Foreign user like 'admin@rabbleinstance.com'
            return tuple(p)
        # Username is incorrect/malicious/etc.
        self._logger.warning('Couldn\'t parse username %s', username)
        return None, None

    def parse_actor(self, actor_uri):
        """
        Given an actor URI, return the (host, handle) tuple for this
        actor.
        """
        actor_doc = self._activ_util.fetch_actor(actor_uri)
        if actor_doc is None:
            self._logger.warning(f'No actor doc found for user {actor_uri}.')
            return None, None
        handle = actor_doc['preferredUsername']
        host = self._activ_util.normalise_hostname(urlparse(actor_uri).netloc)
        return host, handle

    def download_profile_pic(self, host, handle, global_id):
        """
        If a user being added is from a foreign host then get their actor
        and from that download their profile picture to the static assets
        directory. This should all really be a webfinger thing but we don't
        have that option at the time of writing.
        """
        try:
            actor_url = self._activ_util.build_actor(handle, host)
            actor = self._activ_util.fetch_actor(actor_url)

            if "icon" not in actor:
                return  # No profile pic
            pic_url = actor["icon"]["url"]
            self._logger.info("Getting profile pic URL '%s'", pic_url)
            image_resp = requests.get(pic_url)
            if image_resp.status_code < 200 or image_resp.status_code >= 300:
                self._logger.warning(
                    "Could not get profile pic: error %d",
                    image_resp.status_code)
            image_bytes = image_resp.content
            profile_pic_path = "/repo/build_out/chump_dist/user_{}".format(
                global_id)
            self._logger.info("Writing profile pic to %s", profile_pic_path)
            with open(profile_pic_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            self._logger.error("Error when downloading profile pic: %s", str(e))
            # Just pretend that didn't happen

    def _create_user_in_db(self, entry):
        self._logger.debug('Creating user %s@%s in database',
                           entry.handle, entry.host)
        insert_req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.INSERT,
            entry=entry
        )
        insert_resp = self._db.Users(insert_req)
        if insert_resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.error("Error inserting into users db %s",
                               insert_resp.error)
            return None
        return insert_resp.global_id

    def delete_user_from_db(self, global_id):
        self._logger.debug("Deleteing user with global_id %d", global_id)
        resp = self._db.Users(database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.DELETE,
            entry=database_pb2.UsersEntry(
                global_id=global_id
            ),
        ))
        if resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.error("Error deleting from db: %s",
                               resp.error)
            return False
        return True


    def get_or_create_user_from_db(self,
                                   handle=None,
                                   host=None,
                                   global_id=None,
                                   host_is_null=False,
                                   attempt_number=0):
        if attempt_number > MAX_FIND_RETRIES:
            self._logger.error('Retried query too many times.')
            return None

        host = self._activ_util.normalise_hostname(host) if host else host
        user = self.get_user_from_db(handle, host, global_id, host_is_null)

        if user is not None:
            return user

        if global_id is not None or handle is None:
            # Should not try to create a user and hope it has this ID.
            # Also shouldn't create a user with no handle.
            return None

        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
            host_is_null=host_is_null
        )
        new_global_id = self._create_user_in_db(user_entry)
        if new_global_id is not None and host:
            self.download_profile_pic(host, handle, new_global_id)
        return self.get_or_create_user_from_db(handle,
                                               host,
                                               attempt_number=attempt_number + 1)

    def user_is_local(self, global_id):
        user = self.get_user_from_db(global_id=global_id)
        if user is None:
            self._logger.error(
                "Could not get user from DB, "
                "assuming they're foreign and continuing"
            )
            return False
        # Host is empty if user is local.
        return user.host == "" or user.host is None or user.host_is_null

    def get_user_from_db(self, handle=None, host=None, global_id=None, host_is_null=False):
        self._logger.debug('User %s@%s (id %s) host_is_null: %s requested from database',
                           handle, host, global_id, host_is_null)
        host = self._activ_util.normalise_hostname(host) if host else host
        user_entry = database_pb2.UsersEntry(
            handle=handle,
            host=host,
            host_is_null=host_is_null,
            global_id=global_id
        )
        find_req = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.FIND,
            match=user_entry
        )
        find_resp = self._db.Users(find_req)
        if len(find_resp.results) == 0:
            self._logger.warning('No user %s@%s (id %s) found',
                                 handle, host, global_id)
            return None
        elif len(find_resp.results) == 1:
            self._logger.debug('Found user %s@%s (id %s) from database',
                               handle, host, global_id)
            return find_resp.results[0]
        else:
            self._logger.error('> 1 user found in database for %s@%s (id %s)' +
                               ', returning first one.',
                               handle, host, global_id)
            return find_resp.results[0]

    def get_follower_list(self, user_id):
        follow_entry = database_pb2.Follow(
            followed=user_id
        )
        follow_req = database_pb2.DbFollowRequest(
            request_type=database_pb2.DbFollowRequest.FIND,
            match=follow_entry
        )
        follow_resp = self._db.Follow(follow_req)
        if follow_resp.result_type == database_pb2.DbFollowResponse.ERROR:
            self._logger.error(
                "Find for followers of id: %s returned error: %s",
                user_id,
                follow_resp.error
            )
            return []

        return follow_resp.results

    def remove_local_users(self, followers):
        foreign_followers = []
        for follow in followers:
            follower_entry = self.get_user_from_db(
                global_id=follow.follower
            )
            if follower_entry is None:
                self._logger.error("Could not find follower in db. Id: %s", follow.follower)
                continue
            if follower_entry.host:
                foreign_followers.append(follower_entry)
        return foreign_followers
