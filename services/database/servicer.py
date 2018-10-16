import database_pb2

class DatabaseServicer(database_pb2.DatabaseServicer):
    def __init__(self, db):
        self.db = db

    def Posts(self, request, context):
        response = database_pb2.PostsResponse()
        return response

