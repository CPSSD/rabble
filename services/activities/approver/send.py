from services.proto import approver_pb2

class SendApprovalServicer:
    def __init__(self, logger):
        self._logger = logger

    def SendApproval(self, req, context):
        # TODO(devoxel): send approval
        print(req)
        return approver_pb2.ApprovalResponse()
