from services.proto import database_pb2
from services.proto import mdc_pb2


def md_to_html(md, body):
    convert_req = mdc_pb2.MDRequest(md_body=body)
    res = md.MarkdownToHTML(convert_req)
    return res.html_body


def convert_to_tags_string(tags_array):
    # Using | to separate tags. So url encode | character in tags
    tags_array = [x.replace("|", "%7C") for x in tags_array]
    return "|".join(tags_array)


def get_article(logger, db, global_id=None, ap_id=None):
    """
    Retrieve a single PostEntry from the database.
    Returns None on error.
    """
    logger.info("Getting article global_id: %s, ap_id: %s", global_id, ap_id)
    resp = db.Posts(database_pb2.PostsRequest(
        request_type=database_pb2.PostsRequest.FIND,
        match=database_pb2.PostsEntry(
            global_id=global_id,
            ap_id=ap_id,
        )
    ))
    if resp.result_type != database_pb2.PostsResponse.OK:
        logger.error("Error getting article: %s", resp.error)
        return None
    elif len(resp.results) == 0:
        logger.error("Could not find article")
        return None
    return resp.results[0]

def delete_article(logger, db, global_id=None, ap_id=None):
    """
    Deletes and article from the database safely (removing all references).
    Returns True on success and False on error.
    """
    logger.info("Deleting post global_id: %s, ap_id: %s", global_id, ap_id)
    resp = db.SafeRemovePost(database_pb2.PostsEntry(
        global_id=global_id,
        ap_id=ap_id,
    ))
    if resp.result_type != database_pb2.PostsResponse.OK:
        logger.error("Error deleting from DB: %s", resp.error)
        return False
    return True

