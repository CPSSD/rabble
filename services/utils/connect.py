"""connect contains util functions for grpc"""
import os
import grpc
import logging
import sys

DEFAULT_TIMEOUT = 5

def get_future_channel(logger, env_var, port):
    """
    Returns a ready grpc channel without waiting for it to be ready.
    This is ONLY nessary when we have a circular dependency. Should try to
    avoid using this at all costs.

    Arguments:
      logger: Rabble logger
      env_var (str): The name of the environment variable that contains the
      host address
      port (int): The known port for the service you're connecting to.
    """
    service_host = os.environ.get(env_var)
    if not service_host:
        logger.error(f"Environment variable {env_var} not set. Unable to continue.")
        sys.exit(1)
    addr = service_host + ":" + str(port)
    channel = grpc.insecure_channel(addr)
    return channel


def get_service_channel(logger, env_var, port, timeout=DEFAULT_TIMEOUT):
    """
    Returns a ready grpc channel. It will exit the running program if the
    environment variable doesn't exist, or it fails to ready the channel.

    Arguments:
      logger: Rabble logger
      env_var (str): The name of the environment variable that contains the
      host address
      port (int): The known port for the service you're connecting to.
      timeout (int): Timeout to use, default is 30.
    """
    service_host = os.environ.get(env_var)
    if not service_host:
        logger.error(f"Environment variable {env_var} not set. Unable to continue.")
        sys.exit(1)
    addr = service_host + ":" + str(port)
    channel = grpc.insecure_channel(addr)
    future = grpc.channel_ready_future(channel)

    try:
        future.result(timeout=timeout)
    except grpc.FutureTimeoutError:
        logger.error(f"Failed to connect to '{addr}': " +
                     f"timeout reached ({timeout}s).")
        sys.exit(1)

    return channel
