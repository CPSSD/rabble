from send import SendApprovalServicer
from receive import ReceiveApprovalServicer
from services.proto import approver_pb2_grpc

class ApproverServicer(approver_pb2_grpc.ApproverServicer):
    def __init__(self, logger, db_stub, activ_util):
        self._logger = logger

        send = SendApprovalServicer(logger, activ_util)
        self.SendApproval = send.SendApproval
        receive = ReceiveApprovalServicer(logger)
        self.ReceiveApproval = receive.ReceiveApproval
