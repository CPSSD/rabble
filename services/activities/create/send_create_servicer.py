from proto import create_pb2
from proto import database_pb2


class SendCreateServicer:

    def __init__(self, db_stub, logger):
        self._db_stub = db_stub
        self._logger = logger

    def SendCreate(self, request, context):
        self._logger.info('Recieved a new create action.')
        resp = create_pb2.CreateResponse()
        resp.result_type = create_pb2.CreateResponse.OK
        return resp
