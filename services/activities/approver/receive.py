from services.proto import approver_pb2

class ReceiveApprovalServicer:
    def __init__(self, logger):
        self._logger = logger

    def ReceiveApproval(self, req, context):
        # TODO(devoxel): Receive approval logic
        self._logger.info("Received an approval request: %s", req)
        # Here is where we'll set the follower to a real follower
        # or remove the follow from the database
        return approver_pb2.ApprovalResponse()
