class Util:

    def __init__(self, logger):
        self._logger = logger

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
