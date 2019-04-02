from services.proto import database_pb2

def get_post(logger, db, global_id):
    logger.info("Getting post %d", global_id)
    resp = db.Posts(database_pb2.PostsRequest(
        request_type=database_pb2.PostsRequest.FIND,
        match=database_pb2.PostsEntry(
            global_id=global_id,
        )
    ))
    if resp.result_type != database_pb2.PostsResponse.OK:
        logger.error("Error getting post %d: %s", global_id, resp.error)
        return None
    elif len(resp.results) == 0:
        logger.error("Could not find post %d", global_id)
    return resp.results[0]

