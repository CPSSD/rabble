import os
import grpc
import logging
from services.proto import logger_pb2
from services.proto import logger_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from utils.connect import get_service_channel


LOGGER_ENV_VAR = 'LOGGER_SERVICE_HOST'


def get_logger(name, level):
    logger = logging.getLogger(name)
    # The logger should process everything.
    logger.setLevel(logging.DEBUG)
    # The stream out should be filtered.
    sh = logging.StreamHandler()
    sh.setLevel(level)
    logger.addHandler(sh)

    if not os.environ.get(LOGGER_ENV_VAR):
        logger.warning(LOGGER_ENV_VAR,
                       'env var not set, only logging locally')
    else:
        logger.addHandler(GrpcHandler(logger, name))
    return logger


class LoggerConnectionException(Exception):
    pass


class GrpcHandler(logging.Handler):
    def __init__(self, err_logger, source_name, timeout=50):
        super(GrpcHandler, self).__init__()
        self.source_name = source_name
        self.level_to_sev = {
            'DEBUG': logger_pb2.Log.DEBUG,
            'INFO': logger_pb2.Log.INFO,
            'WARNING': logger_pb2.Log.WARNING,
            'ERROR': logger_pb2.Log.ERROR,
            'CRITICAL': logger_pb2.Log.CRITICAL,
        }

        self.channel = get_service_channel(err_logger, LOGGER_ENV_VAR, 1867)
        self.stub = logger_pb2_grpc.LoggerStub(self.channel)

    def emit(self, record):
        t = Timestamp()
        t.seconds = int(record.created)
        sev = self.level_to_sev[record.levelname]
        log = logger_pb2.Log(
            source=self.source_name,
            severity=sev,
            timestamp=t,
            message=record.getMessage())
        self.stub.WriteLog(log)

    def close(self):
        self.channel.close()
        super(GrpcHandler, self).close()

