from services.proto import database_pb2


def convert_to_tags_string(tags_array):
    # Using | to separate tags. So url encode | character in tags
    tags_array = [x.replace("|", "%7C") for x in tags_array]
    return "|".join(tags_array)


def get_article(logger, db, global_id):
    logger.info("Getting article %d", global_id)
    resp = db.Posts(database_pb2.PostsRequest(
        request_type=database_pb2.PostsRequest.FIND,
        match=database_pb2.PostsEntry(
            global_id=global_id,
        )
    ))
    if resp.result_type != database_pb2.PostsResponse.OK:
        logger.error("Error getting article %d: %s", global_id, resp.error)
        return None
    elif len(resp.results) == 0:
        logger.error("Could not find article %d", global_id)
    return resp.results[0]

