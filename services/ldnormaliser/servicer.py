import json
from pyld import jsonld

from services.proto import ldnorm_pb2_grpc
from services.proto import ldnorm_pb2 as lpb2

class LDNormServicer(ldnorm_pb2_grpc.LDNormServicer):
    def __init__(self, logger):
        self._logger = logger
        requests = jsonld.requests_document_loader(timeout=10)
        jsonld.set_document_loader(requests)

    def _norm(self, ld):
        j = json.loads(ld)
        flat = jsonld.flatten(j)
        return json.dumps(flat)

    def Normalise(self, request, context):
        self._logger.debug('Got normalise request for: %s', request.json)
        resp = lpb2.NormaliseResponse(result_type=lpb2.NormaliseResponse.OK)
        try:
            resp.normalised = self._norm(request.json)
        except (Exception, jsonld.JsonLdError) as e:
            # For some reason JsonLdError doesn't inherit from Exception so it
            # has to be caught seperately, it also has a super long message
            # (~20 lines) so I truncate it.
            self._logger.error("JSON-LD could not be normalised: %s", str(e)[:50])
            resp.result_type = lpb2.NormaliseResponse.ERROR
        return resp

