from utils.activities import ActivitiesUtil

def build_like_activity(like_actor, liked_object):
    return {
        "@context":  ActivitiesUtil.rabble_context(),
        'type': 'Like',
        'object': liked_object,
        'actor': {
            'type': 'Person',
            'id': like_actor,
        },
    }

