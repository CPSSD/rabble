import bcrypt

import unittest
from unittest.mock import Mock

from update import UpdateHandler
from services.proto import database_pb2
from services.proto import users_pb2


class MockDBStub:
    def __init__(self):
        self.Users = Mock()


class UpdateHandlerTest(unittest.TestCase):
    def setUp(self):
        self.db_stub = MockDBStub()
        self.update_handler = UpdateHandler(Mock(), self.db_stub)
        self._pw = "hunter2"
        self._pw_hash = bcrypt.hashpw(self._pw.encode('utf-8'),
                                      bcrypt.gensalt())

    def _make_request(self):
        return users_pb2.UpdateUserRequest(
            handle="CianLR",
            current_password=self._pw,
        )

    def _make_user(self, pw=None):
        pw = self._pw_hash if pw is None else pw
        return database_pb2.UsersEntry(
            handle="CianLR",
            global_id=1,
            display_name="Cian Ruane",
            password=pw,
            bio="A sound lad",
        )

    def test_handle_db_error(self):
        req = self._make_request()
        err = "MockError"
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.ERROR,
            error=err,
        )
        resp = self.update_handler.Update(req, None)
        self.assertEqual(resp.result, users_pb2.UpdateUserResponse.ERROR)
        self.assertEqual(resp.error, err)

    def test_handle_no_user(self):
        req = self._make_request()
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[],
        )
        resp = self.update_handler.Update(req, None)
        self.assertEqual(resp.result, users_pb2.UpdateUserResponse.ERROR)

    def test_handle_many_users(self):
        req = self._make_request()
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[self._make_user(), self._make_user()],
        )
        resp = self.update_handler.Update(req, None)
        self.assertEqual(resp.result, users_pb2.UpdateUserResponse.ERROR)

    def test_correct_password(self):
        user = self._make_user()
        user_lookup = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[user],
        )
        user_update = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
        )
        self.db_stub.Users.side_effect = [user_lookup, user_update]

        req = self._make_request()
        resp = self.update_handler.Update(req, None)
        self.assertEqual(resp.result, users_pb2.UpdateUserResponse.ACCEPTED)

    def test_incorrect_password(self):
        req = self._make_request()
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[self._make_user(b"password123")],
        )
        resp = self.update_handler.Update(req, None)
        self.assertEqual(resp.result, users_pb2.UpdateUserResponse.DENIED)

