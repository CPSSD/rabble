
def build_like_activity(like_actor, liked_object):
    return {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'type': 'Like',
        'object': liked_object,
        'actor': {
            'type': 'Person',
            'id': like_actor,
        },
    }

