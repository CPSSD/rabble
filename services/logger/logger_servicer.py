from datetime import datetime
import logging

from services.proto import logger_pb2_grpc
from services.proto import logger_pb2 as lpb2

class LoggerServicer(logger_pb2_grpc.LoggerServicer):
    def __init__(self, logger):
        self._logger = logger
        self._log_levels = {
            lpb2.Log.DEBUG: logging.DEBUG,
            lpb2.Log.INFO: logging.INFO,
            lpb2.Log.WARNING: logging.WARNING,
            lpb2.Log.ERROR: logging.ERROR,
            lpb2.Log.CRITICAL: logging.CRITICAL,
        }

    def _format_log(self, timestamp, source, level, message):
        return ' | '.join([
            datetime.utcfromtimestamp(timestamp.seconds)
                .strftime('%Y-%m-%d %H:%M:%S'),
            source,
            logging.getLevelName(level),
            message])

    def WriteLog(self, request, context):
        py_level = self._log_levels[request.severity]
        log_message = self._format_log(
            request.timestamp, request.source,
            py_level, request.message)
        self._logger.log(py_level, log_message)
        return lpb2.WriteLogResponse(response_type=lpb2.WriteLogResponse.OK)

