import bcrypt

import unittest
from unittest.mock import Mock

from login import LoginHandler
from services.proto import database_pb2
from services.proto import users_pb2


class MockDBStub:
    def __init__(self):
        self.Users = Mock()


class LoginHandlerTest(unittest.TestCase):
    def setUp(self):
        self.db_stub = MockDBStub()
        self.login_handler = LoginHandler(Mock(), self.db_stub)
        self._pw = "hunter2"
        self._pw_hash = bcrypt.hashpw(self._pw.encode('utf-8'),
                                      bcrypt.gensalt())

    def _make_request(self):
        return users_pb2.LoginRequest(
            handle="CianLR",
            password=self._pw,
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
        resp = self.login_handler.Login(req, None)
        self.assertEqual(resp.result, users_pb2.LoginResponse.ERROR)
        self.assertEqual(resp.error, err)

    def test_handle_no_user(self):
        req = self._make_request()
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[],
        )
        resp = self.login_handler.Login(req, None)
        self.assertEqual(resp.result, users_pb2.LoginResponse.ERROR)

    def test_handle_many_users(self):
        req = self._make_request()
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[self._make_user(), self._make_user()],
        )
        resp = self.login_handler.Login(req, None)
        self.assertEqual(resp.result, users_pb2.LoginResponse.ERROR)

    def test_correct_password(self):
        req = self._make_request()
        user = self._make_user()
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[user],
        )
        resp = self.login_handler.Login(req, None)
        self.assertEqual(resp.result, users_pb2.LoginResponse.ACCEPTED)
        self.assertEqual(resp.display_name, user.display_name)
        self.assertEqual(resp.global_id, user.global_id)

    def test_incorrect_password(self):
        req = self._make_request()
        self.db_stub.Users.return_value = database_pb2.UsersResponse(
            result_type=database_pb2.UsersResponse.OK,
            results=[self._make_user(b"password123")],
        )
        resp = self.login_handler.Login(req, None)
        self.assertEqual(resp.result, users_pb2.LoginResponse.DENIED)

