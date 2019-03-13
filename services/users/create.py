import bcrypt
import subprocess

from services.proto import users_pb2
from services.proto import database_pb2

class CreateHandler:
    def __init__(self, logger, db_stub):
        self._logger = logger
        self._db_stub = db_stub

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'),
                             bcrypt.gensalt())

    def _create_public_and_private_key(self):
        public_key_file = 'public.pem'
        private_key_file = 'private.pem'
        self._logger.debug('Creating public and private keys.')
        subprocess.run(['openssl', 'genrsa', '-out', private_key_file, '2048'])
        subprocess.run(['openssl', 'rsa', '-in', private_key_file, '-outform',
                        'PEM', '-pubout', '-out', public_key_file])
        with open(public_key_file, 'r') as f:
            public_key = ''.join(line.strip() for line in f.readlines())
        with open(private_key_file, 'r') as f:
            private_key = ''.join(line.strip() for line in f.readlines())
        self._logger.debug(public_key)
        self._logger.debug(private_key)
        subprocess.run(['rm', public_key_file, private_key_file])
        return public_key, private_key

    def Create(self, request, context):
        public_key, private_key = self._create_public_and_private_key()
        insert_request = database_pb2.UsersRequest(
            request_type=database_pb2.UsersRequest.INSERT,
            entry=database_pb2.UsersEntry(
                handle=request.handle,
                display_name=request.display_name,
                password=self._hash_password(request.password),
                bio=request.bio,
                host_is_null=True,
                public_key=public_key,
                private_key=private_key,
            ),
        )
        db_resp = self._db_stub.Users(insert_request)
        if db_resp.result_type != database_pb2.UsersResponse.OK:
            self._logger.warning("Error inserting user into db: %s",
                                 db_resp.error)
            return users_pb2.CreateUserResponse(
                result_type=users_pb2.CreateUserResponse.ERROR,
                error=db_resp.error,
            )
        return users_pb2.CreateUserResponse(
            result_type=users_pb2.CreateUserResponse.OK,
            global_id=db_resp.global_id,
        )
