import os
import grpc
import logging
import logger_pb2
import logger_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp


LOGGER_ENV_VAR = 'LOGGER_SERVICE_HOST'


def get_logger(name, level):
    logger = logging.getLogger(name)
    # The logger should process everything.
    logger.setLevel(logging.DEBUG)
    # The stream out should be filtered.
    sh = logging.StreamHandler()
    sh.setLevel(level)
    logger.addHandler(sh)
    if LOGGER_ENV_VAR in os.environ:
        logger_addr = os.environ[LOGGER_ENV_VAR] + ':1867'
        logger.addHandler(GrpcHandler(name, logger_addr))
    else:
        logger.warning(LOGGER_ENV_VAR + ' env var not set, ' +
                       'only logging locally')
    return logger


class LoggerConnectionException(Exception):
    pass


class GrpcHandler(logging.Handler):
    def __init__(self, source_name, logger_addr, timeout=5):
        super(GrpcHandler, self).__init__()
        self.source_name = source_name
        self.level_to_sev = {
            'DEBUG': logger_pb2.Log.DEBUG,
            'INFO': logger_pb2.Log.INFO,
            'WARNING': logger_pb2.Log.WARNING,
            'ERROR': logger_pb2.Log.ERROR,
            'CRITICAL': logger_pb2.Log.CRITICAL,
        }
        self.channel = grpc.insecure_channel(logger_addr)
        self.stub = logger_pb2_grpc.LoggerStub(self.channel)
        chan_future = grpc.channel_ready_future(self.channel)
        try:
            chan_future.result(timeout=timeout)
        except grpc.FutureTimeoutError:
            raise LoggerConnectionException(
                "Timed out after {} seconds connecting to {}"
                    .format(timeout, logger_addr))
    
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

    


