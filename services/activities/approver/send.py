from services.proto import approver_pb2

class SendApprovalServicer:
    def __init__(self, logger):
        self._logger = logger

    def _accept_inbox_url(self, request):
        # TODO(devoxel): remove duplicate inbox_url logic
        s = f'{request.follower_host}/@{request.follower_handle}'
        if not s.startswith('http'):
            s = 'http://' + s
        return s

    def _accept_build_actor(self, handle, host):
        # TODO(devoxel): remove duplicate build_actor logic
        s = f'{host}/@{handle}'
        if not s.startswith('http'):
            s = 'http://' + s
        return s
    
    def _accept_follow(self, request):
        followed = self._accept_build_actor(request.followed, self._host_name)
        follower = self._accept_build_actor(request.follower_handle,
                                            request.followed_host)
        d = {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'type': 'Accept',
            'actor': followed,
            'object': follower,
            'to': [followed],
        }
        return d

    def SendApproval(self, req, context):
        # TODO(devoxel): send approval
        print(req)
        return approver_pb2.ApprovalResponse()
