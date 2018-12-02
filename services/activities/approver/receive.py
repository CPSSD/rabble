
class ReceiveApprovalServicer:
    def __init__(self, logger):
        self._logger = logger

    def ReceiveApproval(self, req, context):
        # TODO(devoxel): Receive approval
        return approver_pb2.ApprovalResponse()
