import logging
import unittest
from unittest.mock import Mock

from create import CreateHandler
from proto import database_pb2
from proto import users_pb2


class MockDBStub:
    def __init__(self):
        self.Users = Mock()


class CreateHandlerTest(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.db_stub = MockDBStub()
        self.create_handler = CreateHandler(self.logger, self.db_stub)

    def _make_request(self, handle):
        return users_pb2.CreateRequest(
            handle=handle,
            password="123",
            display_name="myname",
            bio="mybio",
        )

    def test_handle_error(self):
        req = self._make_request("CianLR")
        err = "MockError"
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.ERROR,
            error=err,
        )
        resp = self.create_handler.Create(req, None)
        self.assertEqual(resp.result_type, users_pb2.CreateResponse.ERROR)
        self.assertEqual(resp.error_details, err)

    def test_send_db_request(self):
        req = self._make_request("CianLR")
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
        )
        resp = self.create_handler.Create(req, None)
        self.assertEqual(resp.result_type, users_pb2.CreateResponse.OK)
        self.assertNotEqual(self.db_stub.Users.call_args, None)
        db_req = self.db_stub.Users.call_args[0][0]
        self.assertEqual(db_req.entry.handle, "CianLR")

