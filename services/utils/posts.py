from services.proto import search_pb2


def index(logger, search_stub, post_entry):
    req = search_pb2.IndexRequest(post = post_entry)
    resp = search_stub.Index(req)

    if resp.error:
        logger.warning("Error indexing post: %s", resp.error)

    return resp.result_type == search_pb2.IndexResponse.ResultType.Value("OK")
