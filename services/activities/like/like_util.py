
def build_like_activity(self, like_actor, liked_object):
    return {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'type': 'Like',
        'actor': like_actor,
        'object': liked_object,
    }

