from proto import create_pb2
from proto import database_pb2


class ReceiveCreateServicer:

    def __init__(self, db_stub, logger):
        self._db_stub = db_stub
        self._logger = logger

    def ReceiveCreate(self, req, context):
        self._logger.info('Recieved a new create notification.')

        resp = create_pb2.CreateResponse()
        resp.result_type = create_pb2.CreateResponse.OK
        return resp
